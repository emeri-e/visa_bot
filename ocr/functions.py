import subprocess
import time
import requests
import os

def is_ocr_server_running():
    """Checks if the OCR API is already running."""
    try:
        response = requests.get("http://127.0.0.1:2001/docs", timeout=2)
        return response.status_code == 200
    except requests.ConnectionError:
        return False


def start_ocr_server():
    """Starts the FastAPI OCR server in a separate background process without printing logs."""
    log_file = open(os.path.join('ocr','ocr.log'), 'w')  
    print('starting OCR API....')
    subprocess.Popen(
        ["uvicorn", "ocr.app:app", "--host", "0.0.0.0", "--port", "2001"], #, "--log-level", "critical"],
        stdout=log_file, stderr=log_file
    )
    


def wait_for_server():
    """Waits for the FastAPI server to start."""
    while not is_ocr_server_running():
        time.sleep(1)
    print("OCR API is running...")
