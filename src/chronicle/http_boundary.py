"""HTTP authenticity checks shared by loopback transports, not Core authorization."""

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
import json


class LoopbackRequestHandler(BaseHTTPRequestHandler):
    request_hostnames = frozenset({"127.0.0.1", "localhost"})
    browser_requests = False

    def parse_request(self) -> bool:
        if not super().parse_request():
            return False
        if not self._request_boundary_allowed():
            return False
        if self.command not in {"GET", "POST"}:
            self._boundary_error(HTTPStatus.METHOD_NOT_ALLOWED, "method_not_allowed")
            return False
        return True

    def _request_boundary_allowed(self) -> bool:
        hosts = self.headers.get_all("Host") or []
        port = int(self.server.server_address[1])
        allowed = {
            f"[{host}]:{port}" if ":" in host else f"{host}:{port}"
            for host in self.request_hostnames
        }
        authority = hosts[0].strip().lower() if len(hosts) == 1 else None
        if authority not in allowed:
            self._boundary_error(HTTPStatus.MISDIRECTED_REQUEST, "invalid_host")
            return False
        origins = self.headers.get_all("Origin") or []
        if not self.browser_requests:
            if origins:
                self._boundary_error(HTTPStatus.FORBIDDEN, "origin_not_allowed")
                return False
        elif not origins:
            if self.command != "GET":
                self._boundary_error(HTTPStatus.FORBIDDEN, "origin_required")
                return False
        elif len(origins) != 1 or origins[0].strip().lower() != f"http://{authority}":
            self._boundary_error(HTTPStatus.FORBIDDEN, "origin_not_allowed")
            return False
        return True

    def _boundary_error(self, status: HTTPStatus, error: str) -> None:
        # Close rejected requests without reading their possibly untrusted bodies.
        self.close_connection = True
        payload = json.dumps({"ok": False, "status": "error", "error": error}).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Connection", "close")
        if status == HTTPStatus.METHOD_NOT_ALLOWED:
            self.send_header("Allow", "GET, POST")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)
