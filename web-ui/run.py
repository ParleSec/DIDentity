#!/usr/bin/env python3
"""
Simple script to run the DIDentity Web UI demo
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import streamlit
        import requests
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def main():
    print("🆔 DIDentity Web UI Demo")
    print("=" * 30)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ main.py not found. Please run this script from the web-ui directory.")
        sys.exit(1)
    
    print("🚀 Starting Streamlit web UI...")
    print("📱 The demo will open in your browser at: http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the server")
    print()
    
    # Run Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "main.py",
            "--server.port", "8501",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Stopping DIDentity Web UI...")
    except Exception as e:
        print(f"❌ Error starting web UI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 