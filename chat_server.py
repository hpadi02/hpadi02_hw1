#!/usr/bin/env python3
"""
chat server (cross-platform, python 3)

- accepts one client connection (baseline requirement)
- relays messages between:
    • the server operator typing in stdin (keyboard input)
    • the connected client socket

- on linux/mac: uses the selectors module to watch both stdin and sockets
- on windows: selectors cannot watch stdin, so we use a background thread
  to read from stdin and send it to the client

run:
    python chat_server.py LISTEN_PORT

example:
    python chat_server.py 5000
"""

import sys
import socket
import selectors
import threading
import platform
from typing import Optional


def parse_args() -> tuple[int, str]:
    """
    read the port number and mode from command line arguments.
    exits with error message if input is missing or invalid.
    """
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("usage: python chat_server.py LISTEN_PORT [--line|--char]", file=sys.stderr)
        print("  --line: line-based mode (press Enter to send) - baseline requirement", file=sys.stderr)
        print("  --char: per-character mode (send as you type) - advanced requirement", file=sys.stderr)
        print("  default: --char", file=sys.stderr)
        sys.exit(1)
    
    try:
        port = int(sys.argv[1])
        if not (0 < port < 65536):
            raise ValueError
    except ValueError:
        print("listen_port must be an integer between 1 and 65535", file=sys.stderr)
        sys.exit(1)
    
    # Parse mode (default to char mode)
    mode = "char"
    if len(sys.argv) == 3:
        if sys.argv[2] == "--line":
            mode = "line"
        elif sys.argv[2] == "--char":
            mode = "char"
        else:
            print("invalid mode. use --line or --char", file=sys.stderr)
            sys.exit(1)
    
    return port, mode


class LineBuffer:
    """
    helper to deal with tcp streams.
    tcp does not guarantee that a full line arrives at once.
    this class stores partial data until a newline is found,
    then returns complete text lines.
    """

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[str]:
        # the client is now sending character by character, so the server
        # will receive small chunks of data. this line buffer is still useful
        # if the client sends full lines or the tcp stream fragments the data.
        self._buffer.extend(data)
        lines: list[str] = []
        while True:
            try:
                idx = self._buffer.index(0x0A)  # newline = 0x0a
            except ValueError:
                break  # no full line yet
            line_bytes = self._buffer[: idx + 1]
            del self._buffer[: idx + 1]
            lines.append(line_bytes.decode("utf-8", errors="replace"))
        return lines


def run_server(listen_port: int, mode: str) -> None:
    """main loop for the chat server"""
    sel = selectors.DefaultSelector()

    # create a tcp socket that listens for new connections
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("0.0.0.0", listen_port))   # 0.0.0.0 means all network interfaces
    server_sock.listen(1)                         # only one client for now
    server_sock.setblocking(False)                # non-blocking so selectors works

    print(f"[server] listening on 0.0.0.0:{listen_port}")

    # register the server socket so selectors knows we want to accept new clients
    sel.register(server_sock, selectors.EVENT_READ, data="accept")

    # Use a mutable list to avoid `nonlocal` issues
    client_sock_ref: list[Optional[socket.socket]] = [None]
    client_buf = LineBuffer()

    # helper: background thread to forward stdin to client (windows only)
    def stdin_loop(client_sock_list: list[Optional[socket.socket]]):
        # on Windows, msvcrt.getch() is used to read each character immediately
        import msvcrt
        while True:
            try:
                char = msvcrt.getch()
                if not char:
                    continue
                
                

                # get the socket through the passed-in list
                current_client_sock = client_sock_list[0]
                if current_client_sock is not None:
                    # send the single character to the client
                    current_client_sock.sendall(char)
            except Exception:
                print("[server] failed to send; client disconnected")
                return

    # decide how to handle stdin based on operating system and mode
    if mode == "char":
        # Per-character mode: use raw terminal
        if platform.system() != "Windows":
            # linux/mac: set terminal to raw mode and monitor stdin with selectors
            # these modules are only available on Unix
            import os
            import atexit
            import signal
            import termios
            import tty

            old_termios_settings = None
            try:
                # store current terminal settings and switch to raw mode
                old_termios_settings = termios.tcgetattr(sys.stdin)
                tty.setraw(sys.stdin.fileno())

                # ensure restoration on exit
                def restore_termios():
                    try:
                        if old_termios_settings is not None:
                            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_termios_settings)
                    except Exception:
                        pass
                atexit.register(restore_termios)
            except Exception:
                # if raw mode fails, continue; we'll still try to read bytes
                pass

            sel.register(sys.stdin, selectors.EVENT_READ, data="stdin")
        else:
            # windows: stdin not supported by selectors, so use a background thread
            # Pass the mutable list to the thread
            threading.Thread(target=stdin_loop, args=(client_sock_ref,), daemon=True).start()
    else:
        # Line-based mode: use normal terminal
        sel.register(sys.stdin, selectors.EVENT_READ, data="stdin")

    # main event loop
    try:
        while True:
            # wait until something happens on a registered file/socket
            for key, _ in sel.select(timeout=None):

                if key.data == "accept":
                    # a new client is trying to connect
                    conn, addr = server_sock.accept()
                    # Check the socket reference in the list
                    if client_sock_ref[0] is not None:
                        # already serving one client 
                        conn.sendall(b"server busy. try later.\n")
                        conn.close()
                        continue
                    # Update the socket reference in the list
                    client_sock_ref[0] = conn
                    conn.setblocking(False)
                    sel.register(conn, selectors.EVENT_READ, data="client")
                    print(f"[server] client connected from {addr[0]}:{addr[1]}")

                elif key.data == "client":
                    # incoming data from the client
                    current_client_sock = client_sock_ref[0]
                    assert current_client_sock is not None
                    try:
                        # read data from client
                        data = current_client_sock.recv(4096)
                    except ConnectionResetError:
                        data = b""
                    if not data:
                        # client closed the connection
                        print("[server] client disconnected")
                        sel.unregister(current_client_sock)
                        current_client_sock.close()
                        # Reset the socket reference in the list
                        client_sock_ref[0] = None
                        continue
                    # iterate over data and print in real time
                    sys.stdout.buffer.write(data)
                    sys.stdout.flush()

                elif key.data == "stdin":
                    # server operator typed something
                    current_client_sock = client_sock_ref[0]
                    
                    if mode == "char" and platform.system() != "Windows":
                        # Per-character mode (Unix/macOS): read single byte and forward immediately
                        import os
                        char = os.read(sys.stdin.fileno(), 1)
                        if not char:
                            continue
                        if current_client_sock is not None:
                            try:
                                current_client_sock.sendall(char)
                            except Exception:
                                print("[server] failed to send; client likely disconnected")
                        else:
                            # echo locally even if no client yet
                            sys.stdout.buffer.write(char)
                            sys.stdout.flush()
                    else:
                        # Line-based mode: read full line and send
                        line = sys.stdin.readline()
                        if line == "":
                            continue
                        if current_client_sock is not None:
                            try:
                                current_client_sock.sendall(line.encode("utf-8"))
                            except Exception:
                                print("[server] failed to send; client likely disconnected")
                        else:
                            print("[server] no client connected yet")
    except KeyboardInterrupt:
        print("\n[server] shutting down")
    finally:
        # exit
        try:
            current_client_sock = client_sock_ref[0]
            if current_client_sock is not None:
                sel.unregister(current_client_sock)
                current_client_sock.close()
        except Exception:
            pass
        try:
            sel.unregister(server_sock)
        except Exception:
            pass
        server_sock.close()


if __name__ == "__main__":
    port_arg, mode_arg = parse_args()
    print(f"[server] starting in {mode_arg} mode")
    run_server(port_arg, mode_arg)