"""Lifecycle and quota regression: only the isolated test database is modified."""
from datetime import datetime, timedelta, timezone
import hashlib

from fastapi.testclient import TestClient
from app.main import app
from app.database import conectar
from test_portals_v2 import portal, create, login
from test_lab_v2 import start, switch


def counts():
    with conectar() as conn:
        return (
            conn.execute("SELECT count(*) n FROM sf_workspaces WHERE kind='lab'").fetchone()['n'],
            conn.execute('SELECT coalesce(sum(count),0) n FROM sf_rate_windows').fetchone()['n'],
        )


def exhaust_new_creation_quota():
    clients = []
    for _ in range(10):
        client, who = start()
        clients.append((client, who))
    return clients


def test_valid_start_resumes_without_charging_or_renewing(portal):
    client, who = start()
    cookie = client.cookies.get('sf_lab')
    with conectar() as conn:
        expiry = conn.execute('SELECT expires_at FROM sf_sessions WHERE token_hash=%s', (hashlib.sha256(cookie.encode()).hexdigest(),)).fetchone()['expires_at']
    before = counts()
    for _ in range(12):
        response = client.post('/v2/lab/start')
        assert response.status_code == 200
        assert response.json()['workspace_id'] == who['workspace_id']
        assert not response.headers.get('set-cookie')
    assert counts() == before
    with conectar() as conn:
        assert conn.execute('SELECT expires_at FROM sf_sessions WHERE token_hash=%s', (hashlib.sha256(cookie.encode()).hexdigest(),)).fetchone()['expires_at'] == expiry


def test_session_reads_never_create_and_new_clients_share_only_quota(portal):
    client, who = start()
    before = counts()
    for _ in range(10):
        assert client.get('/v2/session').json()['workspace_id'] == who['workspace_id']
    stranger = TestClient(app, headers={'X-SolicitaFlow-Context': 'lab'})
    assert stranger.get('/v2/session').status_code == 401
    assert counts() == before


def test_limit_has_retry_after_and_valid_sessions_bypass_creation_quota(portal):
    clients = exhaust_new_creation_quota()
    stranger = TestClient(app, headers={'X-SolicitaFlow-Context': 'lab'})
    denied = stranger.post('/v2/lab/start')
    assert denied.status_code == 429
    assert 1 <= int(denied.headers['Retry-After']) <= 3600
    assert 'sessão válida' in denied.json()['detail']
    assert counts()[0] == 10
    before = counts()
    client, who = clients[0]
    assert client.post('/v2/lab/start').json()['workspace_id'] == who['workspace_id']
    assert counts() == before
    assert stranger.get('/v2/cases').status_code == 401


def test_expired_session_never_recovers_workspace_or_bypasses_quota(portal):
    clients = exhaust_new_creation_quota()
    client, who = clients[0]
    with conectar() as conn:
        conn.execute('UPDATE sf_sessions SET expires_at=now()-interval \'1 second\' WHERE workspace_id=%s', (who['workspace_id'],))
    assert client.get('/v2/session').status_code == 401
    assert client.post('/v2/lab/start').status_code == 429
    assert counts()[0] == 10


def test_explicit_new_entry_after_expiry_creates_independent_lab(portal):
    client, who = start()
    case = create(client).json()
    with conectar() as conn:
        conn.execute('UPDATE sf_sessions SET expires_at=now()-interval \'1 second\' WHERE workspace_id=%s', (who['workspace_id'],))
    assert client.get('/v2/cases').status_code == 401
    response = client.post('/v2/lab/start')
    assert response.status_code == 201
    assert response.json()['workspace_id'] != who['workspace_id']
    assert client.get('/v2/cases/'+case['id']).status_code == 404
    with conectar() as conn:
        assert conn.execute('SELECT 1 FROM sf_cases WHERE id=%s', (case['id'],)).fetchone()


def test_restart_uses_existing_role_switch_and_preserves_data_and_clock(portal):
    client, who = start()
    case = create(client).json()
    client.post('/v2/lab/advance', json={'hours': 6})
    switch(client, 'central')
    before = counts()
    restarted = switch(client, 'colaborador')
    assert restarted['workspace_id'] == who['workspace_id']
    assert counts() == before
    assert client.get('/v2/cases/'+case['id']).status_code == 200
    with conectar() as conn:
        assert conn.execute('SELECT clock_hours FROM sf_workspaces WHERE id=%s', (who['workspace_id'],)).fetchone()['clock_hours'] == 6


def test_expired_workspace_cannot_resume_and_role_switch_caps_session_expiry(portal):
    client, who = start()
    with conectar() as conn:
        deadline = datetime.now(timezone.utc)+timedelta(minutes=30)
        conn.execute('UPDATE sf_workspaces SET expires_at=%s WHERE id=%s', (deadline, who['workspace_id']))
    switch(client, 'central')
    with conectar() as conn:
        expiry = conn.execute('SELECT max(expires_at) expiry FROM sf_sessions WHERE workspace_id=%s', (who['workspace_id'],)).fetchone()['expiry']
        assert expiry <= deadline
        conn.execute('UPDATE sf_workspaces SET expires_at=now()-interval \'1 second\' WHERE id=%s', (who['workspace_id'],))
    assert client.get('/v2/session').status_code == 401
    assert client.post('/v2/lab/start').json()['workspace_id'] != who['workspace_id']


def test_local_cookie_cannot_resume_lab_and_lab_cookie_cannot_authenticate_local(portal):
    client, _, _ = portal
    login(client, 'central')
    local_cookie = client.cookies.get('sf_local')
    visitor = TestClient(app, headers={'X-SolicitaFlow-Context': 'lab'}, cookies={'sf_lab': local_cookie})
    assert visitor.get('/v2/session').status_code == 401
    created = visitor.post('/v2/lab/start')
    assert created.status_code == 201
    assert visitor.get('/v2/cases', headers={'X-SolicitaFlow-Context': 'local'}).status_code == 401


def test_retry_after_matches_the_actual_fixed_window_boundary(portal, monkeypatch):
    from app import laboratory
    fixed = datetime.now(timezone.utc).replace(minute=59, second=30, microsecond=250000)
    class FixedDateTime:
        @staticmethod
        def now(tz): return fixed
    monkeypatch.setattr(laboratory, 'datetime', FixedDateTime)
    exhaust_new_creation_quota()
    stranger = TestClient(app, headers={'X-SolicitaFlow-Context': 'lab'})
    denied = stranger.post('/v2/lab/start')
    assert denied.status_code == 429
    assert denied.headers['Retry-After'] == '30'
