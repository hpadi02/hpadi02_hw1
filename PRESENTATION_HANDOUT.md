# HPAD I/O Homework 1: Network Chat Application
## Project Overview & Demo Guide

---

## What This Project Is
A minimal TCP chat application demonstrating socket programming, event-driven I/O, and cross-platform terminal handling.

**Components:**
- `chat_server.py`: TCP server that accepts one client connection
- `chat_client.py`: TCP client that connects to the server
- Real-time, per-character communication in both directions

---

## Key Features We Built

### ✅ Core Functionality
- **Single-client TCP chat** over network sockets
- **Real-time per-character echo** (no waiting for Enter key)
- **Cross-platform support** (macOS, Linux, Windows)
- **Clean disconnect handling** and port conflict management
- **UTF-8 text transport** with proper encoding

### ✅ Technical Implementation
- **Event-driven I/O** using Python's `selectors` module
- **Non-blocking sockets** for responsive communication
- **Raw terminal mode** on Unix systems for immediate keystroke capture
- **Background threads** on Windows for stdin handling
- **Network binding** to `0.0.0.0` for LAN connectivity

---

## How It Works (Architecture)

### Server (`chat_server.py`)
```
1. Creates non-blocking TCP socket on specified port
2. Uses selectors to monitor:
   - Server socket (for new client connections)
   - Client socket (for incoming data)
   - stdin (Unix only, in raw mode for per-character input)
3. Forwards keystrokes immediately to connected client
4. Prints received data directly to stdout
```

### Client (`chat_client.py`)
```
1. Connects to server IP:port
2. Uses selectors to monitor:
   - Server socket (for incoming data)
   - stdin (Unix only, in raw mode)
3. Sends each keystroke immediately to server
4. Displays received bytes instantly (no line buffering)
```

### Cross-Platform Handling
- **Unix/macOS**: `termios` + `tty` for raw terminal mode
- **Windows**: `msvcrt.getch()` in background thread
- **Both**: `selectors` for efficient I/O multiplexing

---

## Demo Instructions

### Same Machine Demo
```bash
# Terminal A (Server)
python3 chat_server.py 5050

# Terminal B (Client)  
python3 chat_client.py 127.0.0.1 5050
```

### Two Computer Demo
```bash
# On Server Computer
# 1. Find IP: ipconfig getifaddr en0 (macOS) or ipconfig (Windows)
# 2. Start server:
python3 chat_server.py 5050

# On Client Computer
python3 chat_client.py <SERVER_IP> 5050
```

### Demo Script
1. **Start both programs** - show connection messages
2. **Type on client** - characters appear instantly on server
3. **Type on server** - characters appear instantly on client  
4. **Disconnect client** (Ctrl+C) - server logs disconnect
5. **Reconnect** - show server accepts new client

---

## Technical Challenges Solved

### Per-Character Transmission
- **Problem**: Terminals normally buffer input until Enter
- **Solution**: Raw terminal mode disables line buffering and local echo
- **Implementation**: `tty.setraw()` on Unix, `msvcrt.getch()` on Windows

### Cross-Platform stdin Handling
- **Problem**: `selectors` can't monitor stdin on Windows
- **Solution**: Background thread reads keystrokes on Windows
- **Result**: Consistent behavior across all platforms

### TCP Stream Handling
- **Problem**: TCP data can arrive fragmented or coalesced
- **Solution**: Write received bytes directly to stdout (no line buffering)
- **Benefit**: True real-time character display

---

## Assignment Compliance

### ✅ Requirements Met
- **Two programs**: `chat_server.py` and `chat_client.py`
- **Network communication**: TCP sockets
- **Command line interface**: `python3 chat_server.py PORT` and `python3 chat_client.py IP PORT`
- **Real-time chat**: Per-character transmission (advanced requirement)
- **Cross-platform**: Works on macOS, Linux, Windows

### ✅ Code Quality
- **Standard library only**: No external dependencies
- **Error handling**: Port conflicts, disconnections, encoding issues
- **Clean shutdown**: Proper socket cleanup and terminal restoration
- **Documentation**: Clear comments and usage instructions

---

## Questions to Ask Other Teams

### Architecture & Design
- How did you handle cross-platform stdin reading? Why `selectors` vs threads?
- How do you ensure per-character transmission instead of line-buffered input?
- Did you consider backpressure or partial writes on sockets?

### Robustness & Error Handling  
- How does your server detect client disconnects or `ConnectionResetError`?
- What happens if the listen port is already in use?
- How do you recover terminal state if the program crashes in raw mode?

### Protocol & Data Handling
- Did you choose UTF-8 text protocol? How do you handle multi-byte characters?
- Do you normalize line endings (LF vs CRLF) or send raw bytes?
- How do you handle TCP stream fragmentation?

### Extensions & Future Work
- If you added multi-client support, how did you handle broadcasting?
- What would you change to add TLS encryption or authentication?
- How would you structure code for pluggable transports?

---

## Known Limitations
- **Single client only** (by design for this assignment)
- **No authentication or encryption** (plain TCP)
- **No backspace handling** on remote end (raw bytes forwarded)
- **No message history** or persistent storage

---

## Files in Project
- `chat_server.py` (229 lines) - TCP server with per-character input
- `chat_client.py` (194 lines) - TCP client with real-time display  
- `README.md` - Setup and usage instructions
- `PRESENTATION_HANDOUT.md` - This document

**Total**: ~400 lines of clean, documented Python code using only standard library.
