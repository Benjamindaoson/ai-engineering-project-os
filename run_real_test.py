"""
Proper integration test using real database and API.
Starts the server and runs the complete cycle.
"""
import subprocess
import time
import sys
import os
from pathlib import Path

def main():
    # Start the API server in background
    print("Starting API server...")
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "apps.api.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    print("Waiting for API to be ready...")
    time.sleep(5)

    try:
        # Run the test
        result = subprocess.run(
            [sys.executable, "test_real_api_cycle.py"],
            capture_output=True,
            text=True,
            timeout=300
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode
    finally:
        # Stop the server
        print("Stopping API server...")
        api_process.terminate()
        api_process.wait(timeout=5)

if __name__ == "__main__":
    sys.exit(main())
