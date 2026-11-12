import time
from urllib.request import urlopen

for attempt in range(40):
    try:
        for url in ['http://127.0.0.1:8000/health','http://127.0.0.1:5173/','http://127.0.0.1:5173/api/health']:
            with urlopen(url,timeout=2) as response:assert response.status==200
        print('Backend, frontend and proxy ready')
        break
    except Exception:
        if attempt==39:raise
        time.sleep(.5)
