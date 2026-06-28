"""OPTIONAL live loader for Neo4j via the HTTP Query API.

Used only when the network policy allows reaching ``*.databases.neo4j.io`` over
HTTPS. We deliberately use the HTTP Query API (not the Bolt driver on :7687)
because HTTPS-only egress proxies block Bolt. The default workflow does not need
this module at all — it emits portable artifacts instead.

Docs: https://neo4j.com/docs/query-api/current/
"""
from __future__ import annotations

import base64

from .config import NEO4J_PASSWORD, NEO4J_QUERY_URL, NEO4J_USER


class Neo4jQueryClient:
    def __init__(self, url: str = NEO4J_QUERY_URL, user: str = NEO4J_USER,
                 password: str = NEO4J_PASSWORD):
        if not url:
            raise ValueError("NEO4J_QUERY_URL is not set (see .env.example).")
        self.url = url
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        self._headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def run(self, statement: str, parameters: dict | None = None) -> dict:
        import httpx

        payload = {"statement": statement}
        if parameters:
            payload["parameters"] = parameters
        resp = httpx.post(self.url, json=payload, headers=self._headers, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def run_script(self, cypher_script: str) -> int:
        """Run a multi-statement script (statements separated by ';')."""
        count = 0
        for stmt in cypher_script.split(";\n"):
            stmt = stmt.strip()
            if not stmt or stmt.startswith("//"):
                continue
            self.run(stmt)
            count += 1
        return count

    def smoke_test(self) -> bool:
        data = self.run("RETURN 1 AS ok")
        # Query API v2 returns {"data": {"values": [[1]]}} shape variants;
        # just assert we got a 2xx with a body.
        return bool(data)
