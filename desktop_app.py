
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import webview

# Use the folder containing this file as the project directory.
PROJECT_DIR = Path(__file__).resolve().parent
APP_FILE = PROJECT_DIR / "app.py"
APP_URL = "http://127.0.0.1:8501"

if not APP_FILE.exists():
    raise FileNotFoundError(f"Could not find app.py at: {APP_FILE}")

# Start the existing Streamlit application.
streamlit_process = subprocess.Popen(
    [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_FILE),
        "--server.address=127.0.0.1",
        "--server.port=8501",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ],
    cwd=str(PROJECT_DIR),
)

def wait_for_streamlit(timeout=60):
    """Wait until the local Streamlit server responds."""
    deadline = time.time() + timeout

    while time.time() < deadline:
        if streamlit_process.poll() is not None:
            raise RuntimeError(
                "Streamlit stopped unexpectedly. "
                "Check the terminal for its error message."
            )

        try:
            with urllib.request.urlopen(APP_URL, timeout=2):
                return True
        except Exception:
            time.sleep(0.5)

    raise TimeoutError(
        "Streamlit did not start within 60 seconds."
    )

try:
    wait_for_streamlit()

    # Open BizPilot AI in its own Windows desktop window.
    webview.create_window(
        "BizPilot AI",
        APP_URL,
        width=1280,
        height=800,
        min_size=(900, 600),
    )

    webview.start()

finally:
    # Stop the Streamlit process when the desktop window closes.
    if streamlit_process.poll() is None:
        streamlit_process.terminate()

        try:
            streamlit_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            streamlit_process.kill()

