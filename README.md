# HPAD Homework 1 — Network Client/Server (Python)

This project implements a baseline networked chat program using Python 3 and standard library sockets. It includes a simple server and client that communicate over TCP. The baseline satisfies the initial requirement (line-based chat). Additional enhancements are outlined for the rest of the team.

## Files
- `chat_server.py`: Line-based socket server. Accepts one client. Relays stdin<->socket.
- `chat_client.py`: Line-based socket client. Connects to server. Relays stdin<->socket.

## Requirements
- Python 3.8+ (standard library only)
- No third-party packages required

## How to Run (per assignment)

### Two Modes Available

**Line-based mode (baseline requirement):**
- Press Enter to send each line
- Normal terminal behavior
- Good for testing and simple chat

**Per-character mode (advanced requirement):**
- Characters appear instantly as you type
- Raw terminal mode (no local echo)
- Real-time communication

### Start the server
```bash
# Line-based mode (baseline)
python3 chat_server.py LISTEN_PORT --line
# example
python3 chat_server.py 5000 --line

# Per-character mode (advanced) - default
python3 chat_server.py LISTEN_PORT --char
# or simply
python3 chat_server.py 5000
```

The server waits for a connection on the given port.

### Start the client
```bash
# Line-based mode (baseline)
python3 chat_client.py SERVER_IP SERVER_PORT --line
# example (same machine)
python3 chat_client.py 127.0.0.1 5000 --line

# Per-character mode (advanced) - default
python3 chat_client.py SERVER_IP SERVER_PORT --char
# or simply
python3 chat_client.py 127.0.0.1 5000
```

**Important:** Both server and client must use the same mode for proper communication.

## Local Testing Tip

### Line-based mode (easier for testing):
```bash
# Terminal A (Server)
python3 chat_server.py 5000 --line

# Terminal B (Client)
python3 chat_client.py 127.0.0.1 5000 --line
```
Type in either window and press Enter. Lines appear on the other side.

### Per-character mode (advanced):
```bash
# Terminal A (Server)
python3 chat_server.py 5000 --char

# Terminal B (Client)
python3 chat_client.py 127.0.0.1 5000 --char
```
Type in either window. Characters appear instantly on the other side (no Enter needed).

## Run on two computers (same network)

1. On the server computer, find its LAN IP:
   - macOS (Wi‑Fi): `ipconfig getifaddr en0`
   - macOS (Ethernet): `ipconfig getifaddr en1`
   - Windows: `ipconfig` → look for IPv4 Address
   - Linux: `hostname -I`

2. Start the server on a free port (example 5050):
```bash
# Line-based mode (easier for testing)
python3 chat_server.py 5050 --line

# Per-character mode (advanced)
python3 chat_server.py 5050 --char
```

3. On the client computer, connect using the server's IP and same port:
```bash
# Line-based mode (must match server)
python3 chat_client.py <SERVER_IP> 5050 --line

# Per-character mode (must match server)
python3 chat_client.py <SERVER_IP> 5050 --char
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
