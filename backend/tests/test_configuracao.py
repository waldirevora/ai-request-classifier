"""Metadados de interface sem banco, segredos ou acesso ao provedor."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.parametrize('enabled,key,expected', [
    ('false', 'CHAVE_FICTICIA', (False, True)),
    ('true', 'CHAVE_FICTICIA', (True, True)),
    ('true', '', (True, False)),
])
def test_configuracao_reflete_processo_sem_expor_chave(monkeypatch, enabled, key, expected):
    monkeypatch.setenv('AI_ENABLED', enabled)
    monkeypatch.setenv('DEEPSEEK_API_KEY', key)
    monkeypatch.setenv('AI_MODEL', 'modelo-ficticio')
    result = TestClient(app).get('/configuracao')
    assert result.status_code == 200
    assert result.json() == {'ai_enabled': expected[0], 'ai_configured': expected[1], 'ai_model': 'modelo-ficticio'}
    assert 'CHAVE_FICTICIA' not in result.text
