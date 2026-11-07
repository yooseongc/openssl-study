"""Run both services as student; stop the container if either service fails."""
import os, secrets, signal, subprocess, time
from pathlib import Path
for stale in Path('/tmp').glob('openssl-study-ide-*.json'): stale.unlink()
os.environ['IDE_BRIDGE_TOKEN'] = secrets.token_urlsafe(32)
children=[]
stopping=False
def stop(*_):
    global stopping
    stopping=True
signal.signal(signal.SIGTERM,stop)
signal.signal(signal.SIGINT,stop)
try:
    children.append(subprocess.Popen(['/usr/local/bin/code-server','--bind-addr','127.0.0.1:8090',
        '--auth','none','--disable-telemetry','--disable-update-check','--disable-proxy','--reconnection-grace-time','20',
        '--user-data-dir','/home/student/ide-data','--extensions-dir','/opt/ide-extensions',
        '/home/student/lab']))
    children.append(subprocess.Popen(['python','/opt/app/server.py']))
    while not stopping and all(child.poll() is None for child in children): time.sleep(0.3)
finally:
    for child in children:
        if child.poll() is None: child.terminate()
    for child in children:
        try: child.wait(timeout=8)
        except subprocess.TimeoutExpired: child.kill(); child.wait()
if not stopping: raise SystemExit(1)
