import uvicorn
import sys
import os

if __name__ == "__main__":
    # Define paths
    ROOT_DIR = os.path.abspath(os.curdir)
    GATEWAY_DIR = os.path.join(ROOT_DIR, "services", "api_gateway")
    SHARED_DIR = os.path.join(ROOT_DIR, "packages", "quant_shared", "src")

    # Set PYTHONPATH for subprocesses
    current_path = os.environ.get("PYTHONPATH", "")
    new_path = f"{GATEWAY_DIR}{os.pathsep}{SHARED_DIR}{os.pathsep}{current_path}"
    os.environ["PYTHONPATH"] = new_path
    
    print(f"Starting API Gateway with PYTHONPATH: {new_path}")
    print(f"Working Directory: {GATEWAY_DIR}")

    # Run Uvicorn
    # app_dir ensures uvicorn looks in services/api_gateway for 'src'
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True, app_dir=GATEWAY_DIR)
