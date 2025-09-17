#!/usr/bin/env python3
"""
chat client (cross-platform, python 3)

- connects to a tcp chat server
- relays between:
    • the server messages (socket input)
    • the user typing in stdin (keyboard input)

- on linux/mac: uses selectors to watch both stdin and socket, doesnt work on windows because select() only works on sockets, not descriptors like stdin
- on windows: uses a background thread for stdin, since selectors
  cannot monitor stdin there
"""

import sys
import socket
import selectors
import threading
import platform
from typing import Tuple, Optional


def parse_args() -> Tuple[str, int]:
    """parse server ip and port from command line"""
    if len(sys.argv) != 3:
        print("usage: python chat_client.py SERVER_IP SERVER_PORT", file=sys.stderr)
        sys.exit(1)
    server_ip = sys.argv[1]
    try:
        server_port = int(sys.argv[2])
        if not (0 < server_port < 65536):
            raise ValueError
    except ValueError:
        print("server_port must be an integer between 1 and 65535", file=sys.stderr)
        sys.exit(1)
    return server_ip, server_port


class LineBuffer:
    """
    helper to handle tcp streams (data may arrive in chunks)
    store data until we see a newline.
    return complete text lines.
    """
    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[str]:
        self._buffer.extend(data)
        lines: list[str] = []
        while True:
            try:
                # we're still using this to receive messages from the server,
                # which are still line-based in this implementation
                idx = self._buffer.index(0x0A)  # found a newline
            except ValueError:
                break
            line_bytes = self._buffer[: idx + 1]
            del self._buffer[: idx + 1]
            lines.append(line_bytes.decode("utf-8", errors="replace"))
        return lines


def run_client(server_ip: str, server_port: int) -> None:
    """main loop for the chat client"""
    sel = selectors.DefaultSelector()

    # connect to the server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))
    sock.setblocking(False)

    print(f"[client] connected to {server_ip}:{server_port}")

    # register the socket so we know when server sends data
    sel.register(sock, selectors.EVENT_READ, data="server")

    recv_buf = LineBuffer()

    # helper: background thread to read stdin and send to server (windows only)
    def stdin_loop():
        # msvcrt provides a way to read a single character from the console
        # without waiting for a newline, effectively achieving raw mode on Windows.
        import msvcrt
        import os
        import signal

        while True:
            try:
                char = msvcrt.getch()
                if not char:
                    continue

                # check for Ctrl+C (b'\x03') to exit gracefully
                if char == b'\x03':
                    print("Exiting...")
                    os.kill(os.getpid(), signal.SIGINT)
                    break
                
                 
            # write the character to the local console
                sys.stdout.buffer.write(char)
                sys.stdout.flush()

        
            

                # send the character immediately
                sock.sendall(char)
            except Exception:
                print("[client] failed to send; server disconnected?")
                return

    # decide how to handle stdin
    # Unix systems (Linux/macOS)
    if platform.system() != "Windows":
        # these modules are only available on Unix
        import termios
        import tty
        import atexit
        import os
        import signal

        old_termios_settings: Optional[list] = None
        try:
            # get current terminal settings to restore them on exit
            old_termios_settings = termios.tcgetattr(sys.stdin)
            # put terminal in raw mode: read char-by-char, no local echo
            tty.setraw(sys.stdin.fileno())

            # ensure settings are restored even if the program crashes
            def restore_termios():
                if old_termios_settings:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_termios_settings)
                    sys.stderr.write("\r\nrestored terminal settings.\r\n")
            atexit.register(restore_termios)

            # in raw mode, Ctrl+C needs to be handled manually
            def signal_handler(sig, frame):
                sys.exit(0)
            signal.signal(signal.SIGINT, signal_handler)

        except Exception as e:
            print(f"[client] failed to set raw terminal mode: {e}", file=sys.stderr)
            pass
        sel.register(sys.stdin, selectors.EVENT_READ, data="stdin")
    # Windows
    else:
        # stdin not supported by selectors, so use a background thread
        threading.Thread(target=stdin_loop, daemon=True).start()

    # main event loop
    try:
        while True:
            for key, _ in sel.select(timeout=None):
                if key.data == "server":
                    # incoming data from server
                    try:
                        data = sock.recv(4096)
                    except ConnectionResetError:
                        data = b""
                    if not data:
                        print("[client] server closed connection")
                        return
                    for line in recv_buf.feed(data):
                        # print the line to the screen, flushing stdout immediately
                        sys.stdout.write(line)
                        sys.stdout.flush()
                elif key.data == "stdin" and platform.system() != "Windows":
                    # user typed something (linux/mac only path)
                    # read a single character from stdin
                    char = os.read(sys.stdin.fileno(), 1)
                    if not char:
                        continue
                    try:
                        # send the character immediately
                        sock.sendall(char)
                    except Exception:
                        print("[client] failed to send; server disconnected?")
                        return
    except KeyboardInterrupt:
        print("\n[client] exiting")
    finally:
        # cleanup when exiting
        try:
            sel.unregister(sock)
        except Exception:
            pass
        sock.close()


if __name__ == "__main__":
    ip, port = parse_args()
    run_client(ip, port)