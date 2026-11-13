"""Render starts this single process. Never starts a local DB, scheduler or Vite."""
from pathlib import Path
import os,sys
from dotenv import load_dotenv
secret=Path('/etc/secrets/solicitaflow.env')
if secret.exists():load_dotenv(secret,override=False)
port=int(os.getenv('PORT','10000'))
if not 1<=port<=65535:raise SystemExit('Invalid PORT')
os.execv(sys.executable,[sys.executable,'-m','uvicorn','app.cloud:create_public_app','--factory','--app-dir','backend','--host','0.0.0.0','--port',str(port),'--workers','1','--limit-concurrency','20','--timeout-keep-alive','5','--timeout-graceful-shutdown','20','--no-proxy-headers','--no-access-log'])
