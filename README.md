# HPAD I/O Homework 1 — Network Client/Server (Python)

This project implements a baseline networked chat program using Python 3 and standard library sockets. It includes a simple server and client that communicate over TCP. The baseline satisfies the initial requirement (line-based chat). Additional enhancements are outlined for the rest of the team.

## Files
- `chat_server.py`: Line-based socket server. Accepts one client. Relays stdin<->socket.
- `chat_client.py`: Line-based socket client. Connects to server. Relays stdin<->socket.

## Requirements
- Python 3.8+ (standard library only)
- No third-party packages required

## How to Run (per assignment)

### Start the server
```bash
# use python3 on macOS/Linux
python3 chat_server.py LISTEN_PORT
# example
python3 chat_server.py 5000
```

The server waits for a connection on the given port.

### Start the client
```bash
# use python3 on macOS/Linux
python3 chat_client.py SERVER_IP SERVER_PORT
# example (same machine)
python3 chat_client.py 127.0.0.1 5000
```

When both are running, whatever you type in one terminal (press Enter to send) should appear on the other terminal.
Per-character streaming is achieved using the termios and tty modules on Linux/macOS, and the msvcrt.getch() function on Windows.

## Local Testing Tip
Open two terminals on the same machine:
- Terminal A: `python3 chat_server.py 5000`
- Terminal B: `python3 chat_client.py 127.0.0.1 5000`

Type in either window and press Enter. Lines appear on the other side.

## Run on two computers (same network)

1. On the server computer, find its LAN IP:
   - macOS (Wi‑Fi): `ipconfig getifaddr en0`
   - macOS (Ethernet): `ipconfig getifaddr en1`
   - Windows: `ipconfig` → look for IPv4 Address
   - Linux: `hostname -I`

2. Start the server on a free port (example 5050):
```bash
python3 chat_server.py 5050
```

3. On the client computer, connect using the server's IP and same port:
```bash
python3 chat_client.py <SERVER_IP> 5050
```

4. If it doesn't connect:
- Ensure both devices are on the same Wi‑Fi/subnet
- Allow "python" through the OS firewall
- Try another high port (e.g., 5051)
- Test reachability: `ping <SERVER_IP>` or `nc -vz <SERVER_IP> 5050`

## Tasks
This repository contains a working baseline with clear comments in the code. Suggested split across four members:

1) Baseline implementation (completed already)
   - `chat_server.py`: single-client, line-based relay using `selectors`.
   - `chat_client.py`: connects and relays using `selectors`.

2) Per-character streaming (completed already)
   - Send data as each keystroke occurs, not only full lines.
   - Use raw terminal mode on Unix (`termios`, `tty`) and disable local echo.
   - Ensure both directions (client and server) handle immediate forwarding.

3) Multi-client broadcast server 
   - Accept multiple clients, maintain a set, broadcast received data to all others.
   - Handle disconnects cleanly and avoid writing to closed sockets.
   - Optionally add simple client identifiers (remote address prefix).

4) Graceful shutdown + polish 
   - Signal handling (SIGINT/SIGTERM) to close sockets and unregister from selector.
   - Add `/quit` command on server stdin to close all clients and exit.
   - Improve UX messages, and document manual test checklist.



## Manual Test Checklist
- Start server, then client; verify connection message.
- Type on client, press Enter; line appears on server.
- Type on server, press Enter; line appears on client.
- Close client (Ctrl+C) and verify server notices disconnect.
- Restart client and connect again.

## Notes
- The code uses `selectors` for responsiveness without threads.
- Network I/O uses UTF-8 text with newline `\n` as delimiter for the baseline.
