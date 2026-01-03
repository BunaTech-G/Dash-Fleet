#!/usr/bin/env python3
"""Quick test of the simplified DashFleet API."""
import json
import sys
import time
from pathlib import Path

# Test imports
try:
    import psutil
    print("✓ psutil imported")
except ImportError:
    print("✗ psutil not found")
    sys.exit(1)

try:
    from flask import Flask
    print("✓ Flask imported")
except ImportError:
    print("✗ Flask not found")
    sys.exit(1)

# Test main.py imports
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from main import (
        collect_stats,
        _health_score,
        _format_bytes_to_gib,
        _format_uptime,
    )
    print("✓ main.py functions imported")
except ImportError as e:
    print(f"✗ Failed to import from main.py: {e}")
    sys.exit(1)

# Test collect_stats
try:
    stats = collect_stats()
    print(f"✓ collect_stats() works")
    print(f"  - Hostname: {stats.get('hostname', 'unknown')}")
    print(f"  - CPU: {stats.get('cpu_percent', '?')}%")
    print(f"  - RAM: {stats.get('ram_percent', '?')}%")
    print(f"  - Disk: {stats.get('disk_percent', '?')}%")
except Exception as e:
    print(f"✗ collect_stats() failed: {e}")
    sys.exit(1)

# Test health score
try:
    health = _health_score(stats)
    print(f"✓ Health score: {health['score']}/100 ({health['status']})")
except Exception as e:
    print(f"✗ Health score failed: {e}")
    sys.exit(1)

print("\n✓ All basic tests passed!")
