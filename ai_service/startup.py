#!/usr/bin/env python3
"""
Startup script for the AI service
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from api import app
import uvicorn

if __name__ == "__main__":
    print("Starting AI Service on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)