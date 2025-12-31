"""
Test unitaire simple pour fleet_agent.py
"""
import unittest
import fleet_agent
import fleet_agent

class TestFleetAgent(unittest.TestCase):
    def test_collect_agent_stats(self):
        stats = fleet_agent.collect_agent_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("cpu_percent", stats)
        self.assertIn("ram_percent", stats)
        self.assertIn("disk_percent", stats)
        self.assertIn("uptime_seconds", stats)
        self.assertGreaterEqual(stats["cpu_percent"], 0)
        self.assertGreaterEqual(stats["ram_percent"], 0)
        self.assertGreaterEqual(stats["disk_percent"], 0)

if __name__ == "__main__":
    unittest.main()
