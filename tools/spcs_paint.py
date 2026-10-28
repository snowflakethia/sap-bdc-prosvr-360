"""Measure first paint through the SPCS endpoint the way a browser loads it: one kept-alive connection, gzip."""
import re
import sys
import time
import http.client
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from spcs_ingress import ingress_token


def first_paint(host, runs=3):
    hdr = {"Authorization": f'Snowflake Token="{ingress_token(host)}"', "Accept-Encoding": "gzip"}
    c = http.client.HTTPSConnection(host, timeout=60)

    def get(p):
        c.request("GET", p, headers=hdr)
        r = c.getresponse()
        return r.status, r.read(), r.getheader("Content-Encoding")

    get("/healthcheck")  # opens the connection and authenticates, as the browser's login redirect does
    out = []
    for _ in range(runs):
        t = time.time()
        _, html, _ = get("/")
        assets = [(a,) + get(a) for a in re.findall(r'(?:src|href)="(/assets/[^"]+)"', html.decode())]
        out.append((time.time() - t, [(a[-10:], len(b), enc) for a, _, b, enc in assets]))
    c.close()
    return out


if __name__ == "__main__":
    for sec, assets in first_paint(sys.argv[1]):
        print(round(sec, 2), assets)
