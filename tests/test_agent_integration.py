"""
Integration test for Fleet Agent with Tray Icon
"""
import subprocess
import sys
import time
import unittest
from pathlib import Path


class TestFleetAgentIntegration(unittest.TestCase):
    """Integration tests for fleet agent."""

    def test_agent_help_output(self):
        """Test that fleet agent shows help correctly."""
        result = subprocess.run(
            [sys.executable, "fleet_agent.py", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=5
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--tray", result.stdout)
        self.assertIn("Agent de reporting fleet", result.stdout)

    def test_agent_syntax(self):
        """Test that agent Python file compiles without syntax errors."""
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", "fleet_agent.py"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=5
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_tray_module_syntax(self):
        """Test that tray module compiles without syntax errors."""
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", "fleet_agent_windows_tray.py"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=5
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)


if __name__ == "__main__":
    unittest.main()
