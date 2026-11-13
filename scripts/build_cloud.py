"""Reproducible production build; backend secrets are excluded from Node's environment."""
from pathlib import Path
import os,subprocess,sys
root=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,'-m','pip','install','-r','backend/requirements.txt'],cwd=root,check=True)
env={k:v for k,v in os.environ.items() if not k.startswith(('PG','AI_','DEEPSEEK','SF_','DATABASE_URL'))}
subprocess.run(['npm','ci'],cwd=root/'frontend',env=env,check=True)
subprocess.run(['npm','run','build'],cwd=root/'frontend',env=env,check=True)
