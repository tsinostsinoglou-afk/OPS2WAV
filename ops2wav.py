#!/usr/bin/env python3
"""
OPS to WAV Audio Converter (for Actions Semiconductor / AIREC Voice Recorders)
==============================================================================
Converts raw .ops audio recording files from voice recorder devices into
standard playable .wav audio files (16,000 Hz, 16-bit Mono PCM).

No proprietary mobile application or cloud sync required.
"""

import sys
import os
import glob
import wave
import struct
import argparse
import ctypes

try:
    import pyogg.opus as opus
except ImportError:
    print("Error: 'pyogg' package is required.")
    print("Please install it using: pip install pyogg")
    sys.exit(1)


def convert_ops_to_wav(ops_path: str, wav_path: str = None) -> bool:
    """
    Decodes an .ops recording file to a standard .wav file.
    
    Format details:
    - Codec: Opus (Wideband 16 kHz Mono)
    - Hardware Flash Sector / Frame Framing: SplitterKA80 (80-byte blocks)
    - Frame duration: 20 ms (320 samples of 16-bit PCM @ 16 kHz = 640 bytes PCM per block)
    """
    if not os.path.isfile(ops_path):
        print(f"[-] File not found: {ops_path}")
        return False

    if wav_path is None:
        base, _ = os.path.splitext(ops_path)
        wav_path = base + ".wav"

    with open(ops_path, "rb") as f:
        data = f.read()

    file_size = len(data)
    if file_size < 80:
        print(f"[-] File too small to contain valid audio frames: {ops_path}")
        return False

    # Initialize 16 kHz Mono Opus Decoder
    error = ctypes.c_int()
    decoder = opus.opus_decoder_create(16000, 1, ctypes.byref(error))
    if error.value != 0 or not decoder:
        print(f"[-] Failed to initialize libopus decoder (error {error.value})")
        return False

    pcm_buffer = (ctypes.c_int16 * 5760)()
    decoded_pcm = bytearray()

    # Locate initial alignment ('KA' marker) if stream started unaligned
    start_pos = 0
    if not data.startswith(b"KA"):
        first_ka = data.find(b"KA")
        if first_ka != -1:
            start_pos = first_ka

    pos = start_pos
    total_blocks = 0
    decoded_blocks = 0
    plc_blocks = 0

    try:
        while pos + 80 <= file_size:
            block = data[pos : pos + 80]
            total_blocks += 1

            # Check for re-synchronization marker
            if not block.startswith(b"KA"):
                next_ka = data.find(b"KA", pos)
                if next_ka != -1 and (next_ka - pos) < 80:
                    pos = next_ka
                    block = data[pos : pos + 80]

            c_block = (ctypes.c_ubyte * 80).from_buffer_copy(block)
            ret = opus.opus_decode(decoder, c_block, 80, pcm_buffer, 5760, 0)

            if ret > 0:
                decoded_pcm.extend(struct.pack(f"<{ret}h", *pcm_buffer[:ret]))
                decoded_blocks += 1
            else:
                # Packet Loss Concealment (PLC) for missing / corrupted blocks
                plc_ret = opus.opus_decode(decoder, None, 0, pcm_buffer, 320, 0)
                if plc_ret > 0:
                    decoded_pcm.extend(struct.pack(f"<{plc_ret}h", *pcm_buffer[:plc_ret]))
                    plc_blocks += 1

            pos += 80

        # Write output WAV file (16,000 Hz, 16-bit Mono PCM)
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(decoded_pcm)

        duration_sec = len(decoded_pcm) / (16000 * 2)
        print(f"[+] Converted: {os.path.basename(ops_path)} -> {os.path.basename(wav_path)}")
        print(f"    Duration: {duration_sec:.2f}s | Decoded: {decoded_blocks} blocks | PLC: {plc_blocks} blocks")
        return True

    finally:
        opus.opus_decoder_destroy(decoder)


def main():
    parser = argparse.ArgumentParser(
        description="Convert voice recorder .ops files to playable .wav audio files."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=".",
        help="Path to an .ops file or directory containing .ops files (default: current directory)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Optional output .wav path (only valid when converting a single file)",
    )

    args = parser.parse_args()

    target = os.path.abspath(args.input)
    if os.path.isdir(target):
        files = glob.glob(os.path.join(target, "**", "*.ops"), recursive=True)
        if not files:
            # Also search for files directly in target
            files = glob.glob(os.path.join(target, "*.ops"))
        if not files:
            print(f"[-] No .ops files found in directory: {target}")
            return

        print(f"Found {len(files)} .ops file(s) to convert:")
        success_count = 0
        for f in files:
            if convert_ops_to_wav(f):
                success_count += 1
        print(f"\n[+] Finished converting {success_count}/{len(files)} files.")

    elif os.path.isfile(target):
        convert_ops_to_wav(target, args.output)
    else:
        print(f"[-] Invalid input path: {target}")


if __name__ == "__main__":
    main()
