#!/usr/bin/env python3
"""Compatibility entry point for the Admin agent watcher."""
from pathlib import Path
import os
import runpy

os.environ.setdefault("AGENT_ID", "admin-agent")
runpy.run_path(str(Path(__file__).with_name("agent-watcher.py")), run_name="__main__")
