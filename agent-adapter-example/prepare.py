#!/usr/bin/env python3
"""Create a machine-local Agent adapter manifest for the reference process."""

import argparse
import json
import os
import sys
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--out", default="example.agent-adapter.json")
args = parser.parse_args()

directory = Path(__file__).resolve().parent
manifest = {
    "schema_version": "autotask.agent-adapter.v1",
    "adapter_id": "example.agent",
    "name": "AutoTask Example Agent",
    "version": "0.1.0",
    "command": sys.executable,
    "args": [str(directory / "adapter.py")],
    "platforms": ["linux", "macos", "windows"],
    "capabilities": {
        "mcp_transports": ["remote", "stdio"],
        "model_config": True,
        "config_formats": ["json"],
    },
}

output = Path(args.out).expanduser()
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
print(f"Wrote {output} using command {manifest['command']!r}")
