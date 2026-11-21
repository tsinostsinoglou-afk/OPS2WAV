#!/usr/bin/env python3
"""
Interactive OPS to WAV Converter & Dependency Installer
======================================================
Provides an interactive menu for:
1. Installing missing dependencies (pyogg, soundfile, ffmpeg via winget/choco)
2. Batch converting .ops recording files from a selected source directory
   to a designated output directory as standard .wav files.
"""

import os
import sys
import glob
import subprocess
import shutil

# Try importing ops2wav logic
try:
    from ops2wav import convert_ops_to_wav
except ImportError:
    convert_ops_to_wav = None


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def check_python_package(pkg_name: str) -> bool:
    try:
        __import__(pkg_name)
        return True
    except ImportError:
        return False


def check_command_installed(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def get_dependency_status():
    status = {}
    status["pyogg"] = check_python_package("pyogg")
    status["soundfile"] = check_python_package("soundfile")
    status["ffmpeg"] = check_command_installed("ffmpeg")
    return status


def install_python_package(pkg: str):
    print(f"\n[*] Installing Python package '{pkg}' via pip...")
    cmd = [sys.executable, "-m", "pip", "install", pkg]
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print(f"[+] Successfully installed '{pkg}'.")
    else:
        print(f"[-] Failed to install '{pkg}'. Please check your network or permissions.")


def install_ffmpeg_windows():
    print("\n[*] Attempting to install FFmpeg via Windows Package Manager (winget)...")
    if check_command_installed("winget"):
        res = subprocess.run(["winget", "install", "--id", "Gyan.FFmpeg", "-e", "--accept-source-agreements", "--accept-package-agreements"])
        if res.returncode == 0:
            print("[+] FFmpeg installed successfully via winget!")
            print("[!] Note: You may need to restart your terminal/PowerShell for PATH changes to take effect.")
            return
        else:
            print("[-] winget installation encountered an issue, trying choco...")

    if check_command_installed("choco"):
        res = subprocess.run(["choco", "install", "ffmpeg", "-y"])
        if res.returncode == 0:
            print("[+] FFmpeg installed successfully via Chocolatey!")
            return

    print("[-] Neither winget nor choco could install FFmpeg automatically.")
    print("    You can download FFmpeg from: https://www.gyan.dev/ffmpeg/builds/")
    print("    Extract it and add the 'bin' folder to your Windows system PATH.")


def install_all_dependencies():
    print("\n" + "=" * 50)
    print("     INSTALLING DEPENDENCIES")
    print("=" * 50)
    
    # 1. Install pyogg
    if not check_python_package("pyogg"):
        install_python_package("pyogg")
    else:
        print("[+] 'pyogg' is already installed.")

    # 2. Install soundfile (optional audio helper)
    if not check_python_package("soundfile"):
        install_python_package("soundfile")
    else:
        print("[+] 'soundfile' is already installed.")

    # 3. Check FFmpeg
    if not check_command_installed("ffmpeg"):
        install_ffmpeg_windows()
    else:
        print("[+] 'ffmpeg' is already installed and available in PATH.")

    input("\nPress Enter to return to main menu...")


def run_conversion_interactive():
    # Verify core decoder is ready
    if not check_python_package("pyogg"):
        print("\n[!] 'pyogg' is required to decode .ops audio files.")
        print("    Please select Option 2 from the main menu first to install dependencies.")
        input("\nPress Enter to continue...")
        return

    # Re-import convert_ops_to_wav if not loaded earlier
    global convert_ops_to_wav
    if convert_ops_to_wav is None:
        try:
            from ops2wav import convert_ops_to_wav
        except Exception as e:
            print(f"[-] Error loading decoder module: {e}")
            input("\nPress Enter to continue...")
            return

    print("\n" + "=" * 50)
    print("     BATCH CONVERT .OPS TO .WAV")
    print("=" * 50)

    # 1. Prompt for Source Folder
    default_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "RECORD")
    if not os.path.exists(default_src):
        default_src = os.getcwd()

    src_prompt = f"Enter Source Folder containing .ops files [Default: {default_src}]: "
    user_src = input(src_prompt).strip().strip('"').strip("'")
    src_dir = user_src if user_src else default_src

    if not os.path.isdir(src_dir):
        print(f"[-] Source folder does not exist: {src_dir}")
        input("\nPress Enter to continue...")
        return

    # Find .ops files
    ops_files = glob.glob(os.path.join(src_dir, "**", "*.ops"), recursive=True)
    if not ops_files:
        ops_files = glob.glob(os.path.join(src_dir, "*.ops"))

    if not ops_files:
        print(f"[-] No .ops files found in '{src_dir}'")
        input("\nPress Enter to continue...")
        return

    print(f"\n[+] Found {len(ops_files)} .ops recording(s) in source directory.")

    # 2. Prompt for Destination Folder
    default_dst = os.path.join(src_dir, "converted_wav")
    dst_prompt = f"Enter Destination Folder for .wav files [Default: {default_dst}]: "
    user_dst = input(dst_prompt).strip().strip('"').strip("'")
    dst_dir = user_dst if user_dst else default_dst

    os.makedirs(dst_dir, exist_ok=True)
    print(f"[+] Output will be saved to: {dst_dir}\n")

    # 3. Perform Conversion
    success_count = 0
    fail_count = 0

    print("-" * 50)
    for idx, ops_path in enumerate(ops_files, 1):
        filename = os.path.basename(ops_path)
        wav_filename = os.path.splitext(filename)[0] + ".wav"
        out_wav_path = os.path.join(dst_dir, wav_filename)

        print(f"[{idx}/{len(ops_files)}] Converting: {filename}...")
        try:
            ok = convert_ops_to_wav(ops_path, out_wav_path)
            if ok:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"[-] Error converting {filename}: {e}")
            fail_count += 1

    print("-" * 50)
    print(f"\n[✓] Completed: {success_count} succeeded, {fail_count} failed.")
    print(f"[✓] Converted WAV files location: {dst_dir}")
    input("\nPress Enter to return to main menu...")


def main_menu():
    while True:
        clear_screen()
        status = get_dependency_status()

        print("=" * 60)
        print("        AIREC / ACTIONS VOICE RECORDER CONVERTER")
        print("=" * 60)
        print(" System Dependency Status:")
        print(f"   [1] Python Opus Decoder (pyogg) : {'[ INSTALLED ]' if status['pyogg'] else '[ MISSING   ]'}")
        print(f"   [2] Audio Library (soundfile)   : {'[ INSTALLED ]' if status['soundfile'] else '[ MISSING   ]'}")
        print(f"   [3] FFmpeg Audio Engine (ffmpeg): {'[ INSTALLED ]' if status['ffmpeg'] else '[ NOT IN PATH ]'}")
        print("=" * 60)
        print(" Menu:")
        print("   1. Convert .ops files to .wav (Prompt Source & Destination)")
        print("   2. Install / Repair Missing Dependencies (pyogg, soundfile, ffmpeg)")
        print("   3. Exit")
        print("=" * 60)

        choice = input("Select an option [1-3]: ").strip()

        if choice == "1":
            run_conversion_interactive()
        elif choice == "2":
            install_all_dependencies()
        elif choice == "3":
            print("\nExiting. Have a great day!")
            break
        else:
            print("\nInvalid choice. Please select 1, 2, or 3.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main_menu()
