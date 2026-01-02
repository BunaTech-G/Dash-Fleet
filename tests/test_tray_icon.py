"""
Test Fleet Agent Tray Icon Initialization
"""
import sys
import unittest
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fleet_agent_windows_tray import TrayAgent
from fleet_agent import create_tray_icon


class TestTrayIcon(unittest.TestCase):
    """Test tray icon functionality."""

    def test_create_tray_icon(self):
        """Test that create_tray_icon returns a valid PIL Image."""
        icon = create_tray_icon()
        self.assertIsNotNone(icon)
        self.assertEqual(icon.size, (64, 64))
        self.assertEqual(icon.mode, "RGB")

    def test_tray_agent_init(self):
        """Test TrayAgent initialization."""
        agent = TrayAgent(machine_id="test-machine", log_file="/tmp/test.log")
        self.assertEqual(agent.machine_id, "test-machine")
        self.assertEqual(agent.log_file, "/tmp/test.log")
        self.assertFalse(agent.is_paused())

    def test_tray_agent_pause_resume(self):
        """Test TrayAgent pause/resume functionality."""
        agent = TrayAgent()
        
        # Initially not paused
        self.assertFalse(agent.is_paused())
        
        # Pause
        agent.set_paused(True)
        self.assertTrue(agent.is_paused())
        
        # Resume
        agent.set_paused(False)
        self.assertFalse(agent.is_paused())


if __name__ == "__main__":
    unittest.main()
