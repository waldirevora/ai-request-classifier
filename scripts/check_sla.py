"""User process scheduler. No systemd/APT, model calls or external notifications."""
from pathlib import Path
import sys,time,argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.database import conectar
from app.workflow import evaluate

def tick():
    with conectar() as conn:
        workspaces=conn.execute("SELECT id FROM sf_workspaces WHERE expires_at IS NULL OR expires_at>now()").fetchall()
    count=0
    for workspace in workspaces:
        with conectar() as conn:count+=evaluate(conn,workspace['id'])['notifications_created']
    print('SLA tick: internal notifications created =',count,flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--interval',type=int,default=60);parser.add_argument('--once',action='store_true');args=parser.parse_args()
    if args.interval<10:raise SystemExit('Minimum interval: 10 seconds')
    while True:
        try:tick()
        except Exception:print('SLA tick failed; retrying on next scheduled interval',file=sys.stderr,flush=True)
        if args.once:break
        time.sleep(args.interval)
