"""Programmatic access to the Command Center's public SPCS endpoint (CP-10 gate).

Key-pair JWT (user BTHIA, key of connection sfseapac_kp) -> /oauth/token exchange scoped to the
ingress host -> 'Authorization: Snowflake Token="..."' on every request.
"""
import base64
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization

ACCOUNT = "SFSEAPAC-SNOWFLAKE_SAP_APJ"
USER = "BTHIA"
KEY = Path.home() / ".snowflake" / "keys" / "bthia_rsa.p8"
HOST = "sfseapac-snowflake-sap-apj.snowflakecomputing.com"


def _jwt():
    key = serialization.load_pem_private_key(KEY.read_bytes(), password=None)
    pub = key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    fp = "SHA256:" + base64.b64encode(hashlib.sha256(pub).digest()).decode()
    now = int(time.time())
    q = f"{ACCOUNT}.{USER}"
    return jwt.encode({"iss": f"{q}.{fp}", "sub": q, "iat": now, "exp": now + 3540}, key, algorithm="RS256")


def ingress_token(endpoint_host):
    body = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                                   "scope": endpoint_host, "assertion": _jwt()}).encode()
    req = urllib.request.Request(f"https://{HOST}/oauth/token", data=body, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode().strip()


class Ingress:
    def __init__(self, endpoint_host):
        self.base = f"https://{endpoint_host}"
        self.auth = f'Snowflake Token="{ingress_token(endpoint_host)}"'

    def request(self, path, data=None, timeout=60):
        h = {"Authorization": self.auth}
        if data is not None:
            h["Content-Type"] = "application/json"
            data = json.dumps(data).encode()
        req = urllib.request.Request(self.base + path, data=data, headers=h, method="POST" if data else "GET")
        t = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, time.time() - t, r.read()


if __name__ == "__main__":
    import sys
    s, sec, b = Ingress(sys.argv[1]).request(sys.argv[2] if len(sys.argv) > 2 else "/healthcheck")
    print(s, round(sec, 2), b[:200])
