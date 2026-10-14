"""
AgentShield Production Launcher
Usage: python start_production.py [--port 8000] [--host 0.0.0.0]
"""

import os
import sys
import subprocess
import argparse
from dotenv import load_dotenv

# Explicitly load .env from project root and backend
project_root = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(project_root, ".env"))
load_dotenv(os.path.join(project_root, "backend", ".env"))

def main():
    parser = argparse.ArgumentParser(description="Start AgentShield Production Server")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 8000)), help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address to bind")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(project_root, "frontend")
    dist_dir = os.path.join(frontend_dir, "dist")
    backend_dir = os.path.join(project_root, "backend")

    # Check if frontend is built
    if not os.path.exists(dist_dir) or not os.path.exists(os.path.join(dist_dir, "index.html")):
        print("[AgentShield] Frontend build not found. Running 'npm run build'...")
        try:
            subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True, shell=True)
            print("[AgentShield] Frontend built successfully.")
        except Exception as e:
            print(f"[AgentShield Warning] Frontend build failed ({e}). Starting API-only mode.")

    # Set working directory to backend
    sys.path.insert(0, backend_dir)
    os.chdir(backend_dir)

    print(f"\n=======================================================")
    print(f"  AgentShield Security Gateway & Action Integrity Gate")
    print(f"  Listening on: http://{args.host}:{args.port}")
    print(f"  API Docs:     http://{args.host}:{args.port}/docs")
    print(f"  Health Check: http://{args.host}:{args.port}/health")
    print(f"=======================================================\n")

    try:
        import uvicorn
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False)
    except ImportError:
        print("[Error] uvicorn is not installed. Please run: pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()
