#!/usr/bin/env python3
"""
Post-install script to download Playwright browsers
"""
import subprocess
import sys

def install_playwright_browsers():
    """Install Playwright browsers after pip install"""
    try:
        print("🌐 Installing Playwright browsers...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("✅ Playwright browsers installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Playwright browsers: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_playwright_browsers() 