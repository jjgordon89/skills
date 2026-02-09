#!/usr/bin/env python3
"""Audio conversion utilities for ElevenLabs TTS skill.

Usage:
    python3 lib/audio_convert.py convert <input> <output>     Convert MP3 to Opus (WhatsApp compatible)
    python3 lib/audio_convert.py concat <output> <file1> <file2> ...   Concatenate audio files
    python3 lib/audio_convert.py convert-and-send <input> <target> [--channel whatsapp]  Convert + send via stdout JSON

Examples:
    python3 lib/audio_convert.py convert /tmp/voice.mp3 /tmp/voice.ogg
    python3 lib/audio_convert.py concat /tmp/final.mp3 /tmp/part1.mp3 /tmp/part2.mp3
"""

import subprocess
import sys
import os
import tempfile
import json


def convert_to_opus(input_path: str, output_path: str = None, bitrate: str = "64k") -> str:
    """Convert audio file to Opus format for WhatsApp compatibility.
    
    Args:
        input_path: Path to input audio file (MP3, WAV, etc.)
        output_path: Path for output .ogg file. If None, auto-generates from input path.
        bitrate: Audio bitrate (default: 64k)
    
    Returns:
        Path to the converted .ogg file
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if output_path is None:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}.ogg"
    
    cmd = [
        "ffmpeg", "-i", input_path,
        "-c:a", "libopus",
        "-b:a", bitrate,
        "-vbr", "on",
        "-application", "voip",
        output_path,
        "-y"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")
    
    if not os.path.exists(output_path):
        raise RuntimeError(f"Output file was not created: {output_path}")
    
    return output_path


def concat_audio(output_path: str, input_files: list, codec: str = "copy") -> str:
    """Concatenate multiple audio files into one.
    
    Args:
        output_path: Path for the concatenated output file
        input_files: List of input file paths
        codec: Audio codec for output (default: "copy" for lossless concat)
    
    Returns:
        Path to the concatenated file
    """
    for f in input_files:
        if not os.path.exists(f):
            raise FileNotFoundError(f"Input file not found: {f}")
    
    # Create concat list file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as listfile:
        for f in input_files:
            listfile.write(f"file '{os.path.abspath(f)}'\n")
        listfile_path = listfile.name
    
    try:
        cmd = [
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", listfile_path,
            "-c", codec,
            output_path,
            "-y"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg concat failed: {result.stderr}")
    finally:
        os.unlink(listfile_path)
    
    return output_path


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "convert":
        if len(sys.argv) < 3:
            print("Usage: audio_convert.py convert <input> [output]")
            sys.exit(1)
        input_path = sys.argv[2]
        output_path = sys.argv[3] if len(sys.argv) > 3 else None
        result = convert_to_opus(input_path, output_path)
        print(f"Converted: {result}")
    
    elif command == "concat":
        if len(sys.argv) < 5:
            print("Usage: audio_convert.py concat <output> <file1> <file2> ...")
            sys.exit(1)
        output_path = sys.argv[2]
        input_files = sys.argv[3:]
        result = concat_audio(output_path, input_files)
        print(f"Concatenated: {result}")
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
