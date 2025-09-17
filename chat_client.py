#!/usr/bin/env python3
"""
Chat Client (baseline, Python 3)

- Connects to a TCP server and relays between local stdin/stdout and the socket using line-based messages.
- This implements the initial requirement and includes comments for remaining tasks for other members.

Run:
    python chat_client.py SERVER_IP SERVER_PORT

Example:
    python chat_client.py 127.0.0.1 5000
"""

import sys
import socket
import selectors
from typing import Tuple


def parse_args() -> Tuple[str, int]:
    if len(sys.argv) != 3:
        print("Usage: python chat_client.py SERVER_IP SERVER_PORT", file=sys.stderr)
        sys.exit(1)
    server_ip = sys.argv[1]
    try:
        server_port = int(sys.argv[2])
        if not (0 < server_port < 65536):
            raise ValueError
    except ValueError:
        print("SERVER_PORT must be an integer in 1..65535", file=sys.stderr)
        sys.exit(1)
    return server_ip, server_port


class LineBuffer:
    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[str]:
        self._buffer.extend(data)
        lines: list[str] = []
        while True:
            try:
                idx = self._buffer.index(0x0A)
            except ValueError:
                break
            line_bytes = self._buffer[: idx + 1]
            del self._buffer[: idx + 1]
            lines.append(line_bytes.decode("utf-8", errors="replace"))
        return lines


def run_client(server_ip: str, server_port: int) -> None:
    """
    Part implemented:
    - Connect to the server
    - Use non-blocking I/O with selectors to relay between stdin and the socket
    - Print server messages to stdout and send typed lines to server
    """

    sel = selectors.DefaultSelector()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))
    sock.setblocking(False)

    print(f"[client] connected to {server_ip}:{server_port}")

    sel.register(sock, selectors.EVENT_READ, data="server")

    try:
        sys.stdin.reconfigure(encoding="utf-8", newline="\n")  # type: ignore[attr-defined]
    except Exception:
        pass
    sel.register(sys.stdin, selectors.EVENT_READ, data="stdin")

    recv_buf = LineBuffer()

    try:
        while True:
            for key, _ in sel.select(timeout=None):
                if key.data == "server":
                    try:
                        data = sock.recv(4096)
                    except ConnectionResetError:
                        data = b""
                    if not data:
                        print("[client] server closed connection")
                        return
                    for line in recv_buf.feed(data):
                        print(line, end="")
                elif key.data == "stdin":
                    line = sys.stdin.readline()
                    if line == "":
                        # EOF; ignore to keep client running, but user can Ctrl+C to quit
                        continue
                    try:
                        sock.sendall(line.encode("utf-8"))
                    except (BrokenPipeError, OSError):
                        print("[client] failed to send; server disconnected?")
                        return
    except KeyboardInterrupt:
        print("\n[client] exiting")
    finally:
        try:
            sel.unregister(sock)
        except Exception:
            pass
        sock.close()


if __name__ == "__main__":
    ip, port = parse_args()
    run_client(ip, port)
