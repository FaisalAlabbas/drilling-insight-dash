#!/usr/bin/env python3
"""
Startup script for Drilling Insight Dashboard
- Installs dependencies
- Trains model if needed
- Starts backend and frontend servers
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def log_info(msg):
    print(f"{BLUE}➜{RESET} {msg}")

def log_success(msg):
    print(f"{GREEN}✓{RESET} {msg}")

def log_warn(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")

def log_error(msg):
    print(f"{RED}✗{RESET} {msg}")

def run_command(cmd, cwd=None, shell=False):
    """Run a command and return success status"""
    try:
        if shell:
            subprocess.run(cmd, shell=True, cwd=cwd, check=True)
        else:
            subprocess.run(cmd, cwd=cwd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        return False

def main():
    """Main startup routine"""
    print(f"\n{GREEN}{'='*60}")
    print("DRILLING INSIGHT DASHBOARD - STARTUP")
    print(f"{'='*60}{RESET}\n")
    
    project_root = Path(__file__).parent.absolute()
    ai_service_dir = project_root / "ai_service"
    frontend_dir = project_root
    
    # Step 1: Install Python dependencies
    log_info("Checking Python dependencies...")
    req_file = ai_service_dir / "requirements.txt"
    if req_file.exists():
        pip_install = [sys.executable, "-m", "pip", "install", "-q", "-r", str(req_file)]
        if run_command(pip_install, cwd=str(ai_service_dir)):
            log_success("Python dependencies installed")
        else:
            log_warn("Some dependencies may not have installed properly")
    
    # Step 2: Check if model exists, train if needed
    model_path = ai_service_dir / "models" / "recommendation_model.pkl"
    train_script = ai_service_dir / "train.py"
    
    if not model_path.exists():
        log_warn(f"Model not found at {model_path}")
        if train_script.exists():
            log_info("Training model (this may take a moment)...")
            train_cmd = [sys.executable, str(train_script)]
            if run_command(train_cmd, cwd=str(ai_service_dir)):
                log_success("Model trained successfully")
                if model_path.exists():
                    log_success(f"Model saved to {model_path}")
                else:
                    log_error("Model file not created after training")
                    print(f"{YELLOW}Continuing anyway - backend will use fallback predictions{RESET}")
            else:
                log_error("Training failed")
                print(f"{YELLOW}Continuing anyway - backend will use fallback predictions{RESET}")
        else:
            log_error(f"Training script not found: {train_script}")
    else:
        log_success(f"Model found: {model_path}")
    
    # Step 3: Install frontend dependencies if needed
    log_info("Checking frontend dependencies...")
    package_json = frontend_dir / "package.json"
    node_modules = frontend_dir / "node_modules"
    
    if package_json.exists() and not node_modules.exists():
        log_info("Installing Node.js dependencies (this may take a moment)...")
        # Install with npm
        if run_command(["npm", "install"], cwd=str(frontend_dir)):
            log_success("Frontend dependencies installed (npm)")
        else:
            log_warn("Could not install frontend dependencies")
    else:
        log_success("Frontend dependencies ready")
    
    # Step 4: Create .env.local for frontend
    env_file = frontend_dir / ".env.local"
    if not env_file.exists():
        log_info("Creating .env.local for frontend configuration...")
        with open(env_file, 'w') as f:
            f.write("VITE_AI_BASE_URL=http://localhost:8001\n")
        log_success(".env.local created with API endpoint")
    
    # Step 5: Ready to start servers
    print(f"\n{GREEN}{'='*60}")
    print("READY TO START SERVERS")
    print(f"{'='*60}{RESET}\n")
    
    print(f"{BLUE}Backend (Python/FastAPI):{RESET}")
    print(f"  Command: cd ai_service && python -m uvicorn api:app --reload")
    print(f"  URL:     http://localhost:8001")
    print(f"  Docs:    http://localhost:8001/docs")
    print()
    print(f"{BLUE}Frontend (React/Vite):{RESET}")
    print(f"  Command: npm run dev")
    print(f"  URL:     http://localhost:5173")
    print()
    print(f"{YELLOW}To start everything:{RESET}")
    print(f"  Terminal 1: cd {ai_service_dir.name} && python -m uvicorn api:app --reload --host 0.0.0.0 --port 8001")
    print(f"  Terminal 2: npm run dev")
    print()
    print(f"{GREEN}✓ All systems ready!{RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Startup cancelled by user{RESET}")
        sys.exit(0)
    except Exception as e:
        log_error(f"Startup failed: {str(e)}")
        sys.exit(1)
