#!/usr/bin/env python3
"""
Chat Server (baseline, Python 3)

- Accepts a single client connection and echoes line-based messages from/to stdin/stdout across the socket.
- This file contains comments indicating what has been implemented (your part) and TODOs for remaining group members.

Run:
    python chat_server.py LISTEN_PORT

Test locally with two terminals:
    1) Terminal A: python chat_server.py 5000
    2) Terminal B: python chat_client.py 127.0.0.1 5000
Type text in either side and press Enter to send.

Notes:
- Baseline uses a single client and line-delimited messages (\n). This satisfies the initial requirement before per-character streaming and multi-client features.
- Keep dependencies limited to Python standard library per assignment.
"""

import sys
import socket
import selectors
from typing import Optional


def parse_args() -> int:
    if len(sys.argv) != 2:
        print("Usage: python chat_server.py LISTEN_PORT", file=sys.stderr)
        sys.exit(1)
    try:
        port = int(sys.argv[1])
        if not (0 < port < 65536):
            raise ValueError
        return port
    except ValueError:
        print("LISTEN_PORT must be an integer in 1..65535", file=sys.stderr)
        sys.exit(1)


class LineBuffer:
    """Utility to accumulate bytes and produce complete lines separated by \n."""

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[str]:
        self._buffer.extend(data)
        lines: list[str] = []
        while True:
            try:
                idx = self._buffer.index(0x0A)  # \n
            except ValueError:
                break
            line_bytes = self._buffer[: idx + 1]
            del self._buffer[: idx + 1]
            try:
                lines.append(line_bytes.decode("utf-8", errors="replace"))
            except Exception:
                lines.append(line_bytes.decode("utf-8", errors="replace"))
        return lines


def run_server(listen_port: int) -> None:
    """
    Part implemented:
    - Create a TCP listening socket
    - Accept a single client connection
    - Relay between server stdin and the connected client using non-blocking I/O (selectors)
    - Print received client messages to server stdout
    - Send lines typed on server stdin to client

    """

    sel = selectors.DefaultSelector()

    # Create listening socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow quick restart during development
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("0.0.0.0", listen_port))
    server_sock.listen(1)
    server_sock.setblocking(False)

    print(f"[server] listening on 0.0.0.0:{listen_port}")

    sel.register(server_sock, selectors.EVENT_READ, data="accept")

    client_sock: Optional[socket.socket] = None
    client_buf = LineBuffer()

    # Register stdin for non-blocking read using file descriptor 0
    try:
        sys.stdin.reconfigure(encoding="utf-8", newline="\n")  # type: ignore[attr-defined]
    except Exception:
        pass
    sel.register(sys.stdin, selectors.EVENT_READ, data="stdin")

    try:
        while True:
            for key, _ in sel.select(timeout=None):
                if key.data == "accept":
                    # Accept at most one client (baseline requirement)
                    conn, addr = server_sock.accept()
                    if client_sock is not None:
                        # Already connected: politely refuse extra client for baseline
                        conn.sendall(b"Server busy. Try later.\n")
                        conn.close()
                        continue
                    client_sock = conn
                    client_sock.setblocking(False)
                    sel.register(client_sock, selectors.EVENT_READ, data="client")
                    print(f"[server] client connected from {addr[0]}:{addr[1]}")

                elif key.data == "client":
                    assert client_sock is not None
                    try:
                        data = client_sock.recv(4096)
                    except ConnectionResetError:
                        data = b""
                    if not data:
                        print("[server] client disconnected")
                        sel.unregister(client_sock)
                        client_sock.close()
                        client_sock = None
                        continue
                    for line in client_buf.feed(data):
                        # Echo received line to server stdout
                        # (Baseline behavior for simple verification)
                        print(line, end="")

                elif key.data == "stdin":
                    # Read a line from server operator and send to client if connected
                    line = sys.stdin.readline()
                    if line == "":
                        # EOF; continue loop to keep server running
                        continue
                    if client_sock is not None:
                        try:
                            client_sock.sendall(line.encode("utf-8"))
                        except (BrokenPipeError, OSError):
                            print("[server] failed to send; client likely disconnected")
                    else:
                        print("[server] no client connected yet")
    except KeyboardInterrupt:
        print("\n[server] shutting down")
    finally:
        try:
            if client_sock is not None:
                sel.unregister(client_sock)
                client_sock.close()
        except Exception:
            pass
        try:
            sel.unregister(server_sock)
        except Exception:
            pass
        server_sock.close()


if __name__ == "__main__":
    port_arg = parse_args()
    run_server(port_arg)

"""
Remaining tasks:

1) Upgrade to per-character streaming:
   - Currently we send/receive when a full line (ending with \n) is available.
   - Modify both server and client to forward each keystroke immediately.


2) Multi-client support with broadcast:
   - Accept many clients and broadcast each received message/character to all others.
   - Manage client set with selector; remove on disconnect.
   - Consider prefixing messages with client id or remote address.

3) Graceful shutdown and signals:
   - Handle SIGINT/SIGTERM to close all sockets cleanly.
   - Optionally add "/quit" command from server stdin to terminate.

4) Testing & README polish:
   - Add manual test checklist or minimal automated script.
   - Verify behavior on Linux target environment.
"""
