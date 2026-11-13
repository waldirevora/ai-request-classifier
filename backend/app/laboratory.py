"""Fictional visitors resume only by a valid session, never by IP or workspace ID."""
import hashlib
import math
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Request, Response, Depends, HTTPException
from pydantic import BaseModel, Field

from app.database import conectar
from app.identity import actor, context, rate_limit, issue_session, public_actor
from app.bootstrap import seed
from app.workflow import ensure_policies, evaluate, now_for

router = APIRouter(prefix="/v2/lab", tags=["Laboratório fictício"])


def lab_only(who):
    if who["kind"] != "lab":
        raise HTTPException(403, "Operação exclusiva do laboratório fictício")


@router.post("/start", status_code=201)
def start(request: Request, response: Response):
    if context(request) != "lab":
        raise HTTPException(400, "Selecione o contexto do laboratório")

    # An authenticated continuation is a read, not a new creation attempt.
    # No token is renewed here: the original session/workspace deadlines still apply.
    try:
        who = actor(request)
    except HTTPException as error:
        if error.status_code != 401:
            raise
    else:
        lab_only(who)
        response.status_code = 200
        return public_actor(who)

    now = datetime.now(timezone.utc)
    with conectar() as conn:
        allowed = rate_limit(conn, "lab-start:" + request.client.host, 10, now=now)
    if not allowed:
        seconds = max(1, math.ceil(3600 - now.timestamp() % 3600))
        raise HTTPException(
            429,
            "Muitas demonstrações novas foram iniciadas nesta rede. "
            "Uma sessão válida ainda pode ser retomada. Aguarde para criar outra.",
            headers={"Retry-After": str(seconds)},
        )

    with conectar() as conn:
        workspace, _ = seed(
            conn, "lab", "Visitante · Empresa Horizonte fictícia",
            now + timedelta(hours=24),
        )
        ensure_policies(conn, workspace)
        who = conn.execute(
            "SELECT a.*,'lab' AS kind FROM sf_accounts a "
            "WHERE workspace_id=%s AND role='colaborador'", (workspace,),
        ).fetchone()
        issue_session(conn, who, response, "lab")
    return public_actor(who)


@router.get("/actors")
def actors(who=Depends(actor)):
    lab_only(who)
    with conectar() as conn:
        return conn.execute(
            "SELECT username,display_name,role,department_id FROM sf_accounts "
            "WHERE workspace_id=%s ORDER BY role,username", (who["workspace_id"],),
        ).fetchall()


class Switch(BaseModel):
    username: str = Field(min_length=1, max_length=80)


@router.post("/switch")
def switch(data: Switch, request: Request, response: Response, who=Depends(actor)):
    lab_only(who)
    with conectar() as conn:
        target = conn.execute(
            "SELECT a.*,'lab' AS kind FROM sf_accounts a WHERE workspace_id=%s "
            "AND username=%s AND password_hash IS NULL", (who["workspace_id"], data.username),
        ).fetchone()
        if not target:
            raise HTTPException(404, "Personagem fictício não encontrado neste laboratório")
        issue_session(conn, target, response, "lab")
        conn.execute("DELETE FROM sf_sessions WHERE token_hash=%s", (
            hashlib.sha256(request.cookies["sf_lab"].encode()).hexdigest(),
        ))
    return public_actor(target)


class Advance(BaseModel):
    hours: int = Field(ge=1, le=720)


@router.post("/advance")
def advance(data: Advance, who=Depends(actor)):
    lab_only(who)
    with conectar() as conn:
        row = conn.execute(
            "UPDATE sf_workspaces SET clock_hours=clock_hours+%s "
            "WHERE id=%s AND clock_hours+%s<=8760 RETURNING clock_hours",
            (data.hours, who["workspace_id"], data.hours),
        ).fetchone()
        if not row:
            raise HTTPException(422, "Limite de um ano de tempo simulado atingido")
        result = evaluate(conn, who["workspace_id"])
    return {**result, "clock_hours": row["clock_hours"]}


@router.get("/clock")
def clock(who=Depends(actor)):
    lab_only(who)
    with conectar() as conn:
        return {"effective_now": now_for(conn, who["workspace_id"])}
