"""Diagnose Advisor streaming through SPCS ingress: timestamps of SSE events, largest gap, where it ends."""
import json
import sys
import time
import http.client
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from spcs_ingress import ingress_token

host, q = sys.argv[1], sys.argv[2]
c = http.client.HTTPSConnection(host, timeout=300)
c.request("POST", "/api/advisor", body=json.dumps({"messages": [{"role": "user", "text": q}]}),
          headers={"Authorization": f'Snowflake Token="{ingress_token(host)}"', "Content-Type": "application/json"})
r = c.getresponse()
t0 = time.time()
last, gap, n, kinds, end = t0, (0.0, 0.0), 0, {}, "eof"
try:
    while True:
        line = r.readline()
        if not line:
            break
        now = time.time()
        if line.startswith(b"event:"):
            k = line[6:].strip().decode()
            kinds[k] = kinds.get(k, 0) + 1
            n += 1
            if now - last > gap[0]:
                gap = (now - last, last - t0)
            last = now
except Exception as e:
    end = repr(e)[:80]
print(f"status {r.status}; {n} events in {time.time() - t0:.1f} s; largest gap {gap[0]:.1f} s starting at {gap[1]:.1f} s; "
      f"last event at {last - t0:.1f} s; end: {end}")
print(sorted(kinds.items(), key=lambda x: -x[1])[:8])
