import unittest
from main import app


 
class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.token = "testtoken"  # À adapter selon votre config

    
    def test_fleet_report_unauthorized(self):
        resp = self.app.post("/api/fleet/report", json={})
        self.assertEqual(resp.status_code, 403)

    
    def test_create_org_unauthorized(self):
        resp = self.app.post("/api/orgs", json={})
        self.assertEqual(resp.status_code, 403)

    
    def test_action_unauthorized(self):
        resp = self.app.post("/api/action", json={})
        self.assertEqual(resp.status_code, 403)


if __name__ == "__main__":
    unittest.main()
