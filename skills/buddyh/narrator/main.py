#!/usr/bin/env python3
"""
Narrator CLI - Send screenshots to socket server for analysis.
"""

import argparse
import os
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path

SOCKET_PATH = '/tmp/narrator_socket.sock'
SCREENSHOT_PATH = Path('/tmp/narrator_screenshot.png')


def capture_screenshot():
    """Capture a screenshot using available macOS tools."""
    # Try screencapture first (macOS), fall back to ImageMagick import.
    methods = [
        ['screencapture', '-x', str(SCREENSHOT_PATH)],
        ['import', '-window', 'root', str(SCREENSHOT_PATH)],
    ]

    for cmd in methods:
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            break
        except FileNotFoundError:
            continue
        except subprocess.CalledProcessError:
            if SCREENSHOT_PATH.exists():
                SCREENSHOT_PATH.unlink()
            continue
    else:
        raise RuntimeError(
            "No supported screenshot utility found (screencapture/import). "
            "Install ImageMagick or run in a full macOS GUI session."
        )

    with open(SCREENSHOT_PATH, 'rb') as f:
        data = f.read()
    SCREENSHOT_PATH.unlink()
    return data


def get_active_app():
    """Get currently active app and window title."""
    try:
        result = subprocess.run(
            ['osascript', '-e', '''
                tell application "System Events"
                    set frontApp to name of first process whose frontmost is true
                    tell process frontApp
                        set frontWin to name of window 1
                    end tell
                    return frontApp & "\n" & frontWin
                end tell
            '''],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.strip().split('\n')
        return lines[0], lines[1] if len(lines) > 1 else ''
    except Exception:
        return 'Unknown', ''


def send_for_narration(png_bytes, app_name, window_title):
    """Send screenshot to socket server and read narration."""
    if not os.path.exists(SOCKET_PATH):
        print(f"❌ Socket not found: {SOCKET_PATH}", file=sys.stderr)
        print("   Start the server first: python3 server.py", file=sys.stderr)
        return None

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(SOCKET_PATH)

        # Send size then bytes
        sock.sendall(struct.pack('>I', len(png_bytes)))
        sock.sendall(png_bytes)
        sock.sendall((app_name + '\n').encode('utf-8'))
        sock.sendall((window_title + '\n').encode('utf-8'))

        # Get narration
        narration = sock.recv(4096).decode('utf-8')
        sock.close()
        return narration
    except Exception as e:
        print(f"❌ Socket error: {e}", file=sys.stderr)
        return None


def clawtto_mode(mode='normal'):
    """Continuous Clawtto mode - narrate screen activity."""
    mode_name = '🎙️ NORMAL' if mode == 'normal' else '🎃 HORROR'
    print(f"{mode_name} mode activated!")
    print("   (Press Ctrl+C to stop)\n")

    horror_phrases = [
        "the cursor moves toward the dark abyss of the terminal...",
        "oh no, a DELETE button! Will it survive?!",
        "the screen flickers... something ancient awakens...",
        "they're typing a command... whatHaveYouDone.exe",
        "the terminal opens its maw, hungry for input...",
        "darkness fills the command line... a segfault emerges...",
        "the cursor hovers... it knows... it KNOWS!",
        "compiling... always compiling... neverending...",
        "a bash script emerges from the shadows...",
        "the ghost of processes past haunts this terminal...",
        "Ctrl+C won't save them now...",
        "sudo... the forbidden word is spoken!",
    ]

    normal_phrases = [
        "and they're coding like a boss!",
        "magic happening right before our eyes!",
        "absolutely crushing it in VS Code!",
        "look at that syntax highlighting GO!",
        "they're in the zone. Pure productivity!",
        "another line of code drops in cleanly!",
    ]

    phrases = horror_phrases if mode == 'horror' else normal_phrases
    phrase_idx = 0

    while True:
        try:
            png_bytes = capture_screenshot()
            app, window = get_active_app()

            narration = send_for_narration(png_bytes, app, window)

            if narration:
                # Fallback line from client side for deterministic behavior
                if narration.startswith("And they're looking at"):
                    phrase = phrases[phrase_idx % len(phrases)]
                    phrase_idx += 1
                    print(f"   {'🎃' if mode == 'horror' else '🎙️'} \"{phrase}\"")
                else:
                    print(f"   🎙️ {narration}")

            time.sleep(3)  # Narrate every 3 seconds

        except KeyboardInterrupt:
            print("\n👋 Narrator signing off!")
            break
        except RuntimeError as e:
            print(f"⚠️ {e}", file=sys.stderr)
            return
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            time.sleep(5)


def single_shot():
    """Single screenshot narration."""
    print("📸 Capturing screenshot...")

    try:
        png_bytes = capture_screenshot()
    except RuntimeError as e:
        print(f"⚠️ {e}", file=sys.stderr)
        return

    app, window = get_active_app()

    print(f"   App: {app}")
    print(f"   Window: {window}")

    narration = send_for_narration(png_bytes, app, window)

    if narration:
        print(f"\n🎙️ {narration}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Narrator - screen commentary CLI')
    parser.add_argument('--clawtto', action='store_true', help='Continuous Clawtto mode')
    parser.add_argument('--horror', action='store_true', help='Horror announcer mode')

    args = parser.parse_args()

    if args.clawtto or args.horror:
        mode = 'horror' if args.horror else 'normal'
        clawtto_mode(mode)
    else:
        single_shot()
