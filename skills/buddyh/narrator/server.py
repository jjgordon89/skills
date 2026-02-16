#!/usr/bin/env python3
"""
Narrator Socket Server
Listens on /tmp/narrator_socket.sock for screenshot analysis requests.

This implementation intentionally keeps the default path offline-safe:
- returns a deterministic caption fallback unless explicitly configured for AI backend later.
"""

import os
import socket
import struct
import sys

SOCKET_PATH = '/tmp/narrator_socket.sock'


def analyze_screenshot(png_bytes, app_name, window_title):
    """
    Analyze screenshot + context and return a short narration line.

    Note: The shipped baseline is conservative and does not perform network calls.
    It uses the app/window metadata as a fallback caption source.
    """
    target = window_title or app_name
    if target.strip():
        return f"And they're looking at {target}"
    return "And they're working on their screen."


def handle_client(conn):
    """Handle incoming connection from narrator client."""
    try:
        # Read PNG size (4 bytes, big-endian)
        size_data = conn.recv(4)
        if len(size_data) < 4:
            return

        png_size = struct.unpack('>I', size_data)[0]

        # Read PNG bytes
        png_bytes = b''
        while len(png_bytes) < png_size:
            chunk = conn.recv(min(8192, png_size - len(png_bytes)))
            if not chunk:
                return
            png_bytes += chunk

        # Read app name (newline-terminated)
        app_name = b''
        while not app_name.endswith(b'\n'):
            chunk = conn.recv(1)
            if not chunk:
                break
            app_name += chunk
        app_name = app_name.decode('utf-8', errors='replace').strip()

        # Read window title (newline-terminated)
        window_title = b''
        while not window_title.endswith(b'\n'):
            chunk = conn.recv(1)
            if not chunk:
                break
            window_title += chunk
        window_title = window_title.decode('utf-8', errors='replace').strip()

        # Analyze and get narration
        narration = analyze_screenshot(png_bytes, app_name, window_title)

        # Send back narration
        conn.sendall(narration.encode('utf-8'))

    except Exception as e:
        print(f"Error handling client: {e}", file=sys.stderr)
        try:
            conn.sendall(b'Error analyzing screenshot')
        except Exception:
            pass
    finally:
        conn.close()


def main():
    """Start the socket server."""
    # Clean up old socket
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(SOCKET_PATH)
    server.listen(5)

    print(f"📺 Narrator server listening on {SOCKET_PATH}", file=sys.stdout)

    while True:
        conn, _ = server.accept()
        handle_client(conn)


if __name__ == '__main__':
    main()
