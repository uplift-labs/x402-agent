#!/usr/bin/env python3
"""Build script for creating executable with PyInstaller."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

def main():
    """Build the executable and copy required files."""
    script_dir = Path(__file__).parent
    dist_dir = script_dir / 'dist'
    build_dir = script_dir / 'build'
    
    # Clean previous builds
    if dist_dir.exists():
        print("Cleaning previous dist directory...")
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        print("Cleaning previous build directory...")
        shutil.rmtree(build_dir)
    
    # Build with PyInstaller using spec file
    print("Building executable with PyInstaller...")
    spec_file = script_dir / 'web3-agent.spec'
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        str(spec_file)
    ]
    
    result = subprocess.run(cmd, cwd=script_dir)
    if result.returncode != 0:
        print("❌ PyInstaller build failed!")
        sys.exit(1)
    
    # Copy data.json to dist directory (it will also be bundled in the exe)
    # Note: .env is bundled inside the exe and not copied to dist
    print("Copying data.json to dist directory...")
    exe_dir = dist_dir
    
    # Copy data.json
    data_json_src = script_dir / 'data.json'
    if data_json_src.exists():
        shutil.copy2(data_json_src, exe_dir / 'data.json')
        print(f"✓ Copied data.json to {exe_dir / 'data.json'}")
    else:
        print("⚠ Warning: data.json not found in project directory")
        print("  The exe will extract it from the bundle on first run")
    
    # Check if .env exists (it will be bundled in the exe, not copied to dist)
    env_src = script_dir / '.env'
    if env_src.exists():
        print("✓ .env will be bundled inside the exe (not visible in dist)")
    else:
        print("⚠ Warning: .env not found in project directory")
        print("  The exe will not have .env bundled")
    
    print(f"\n✅ Build complete! Executable is at: {exe_dir / 'web3-agent.exe'}")
    print(f"   - data.json: Will be extracted to exe directory on first run")
    print(f"   - .env: Bundled inside the exe (not visible)")

if __name__ == '__main__':
    main()

