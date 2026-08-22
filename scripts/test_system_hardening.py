#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEXA — Automated System Hardening & Security Verification Test Suite
Runs an exhaustive battery of tests across:
- SQLite WAL mode & schema integrity
- Security (Path Traversal, IP Spoofing, CSRF/Origin, Admin Brute Force)
- AI & RAG Function Calling & Delimiter Protections
- Sales Mining & Sync Pipelines
- Frontend HTML & API contract fidelity
"""

import os
import sys
import json
import sqlite3
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

class TestNexaSystemHardening(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ["TESTING"] = "1"
        os.environ["ADMIN_PIN"] = "nexa2026vip"
        import app
        cls.app_module = app
        cls.client = app.app.test_client()

    def test_01_sqlite_wal_mode_and_audit_logs_table(self):
        """Verify SQLite database operates in WAL mode and audit_logs table exists."""
        db_path = ROOT_DIR / "nexa_database.db"
        self.assertTrue(db_path.exists(), "Database file must exist")
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        
        cur.execute("PRAGMA journal_mode;")
        journal_mode = cur.fetchone()[0].lower()
        self.assertEqual(journal_mode, "wal", "Database must be in WAL mode")
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs';")
        self.assertIsNotNone(cur.fetchone(), "audit_logs table must exist")
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_projects_cb_url';")
        self.assertIsNotNone(cur.fetchone(), "idx_projects_cb_url must exist")
        
        conn.close()

    def test_02_client_ip_parsing_and_spoof_prevention(self):
        """Verify _get_client_ip safely parses headers and avoids client spoofing."""
        with self.app_module.app.test_request_context(headers={"CF-Connecting-IP": "203.0.113.195"}):
            ip = self.app_module._get_client_ip()
            self.assertEqual(ip, "203.0.113.195")

        with self.app_module.app.test_request_context(headers={"X-Forwarded-For": "10.0.0.1, 198.51.100.42"}):
            ip = self.app_module._get_client_ip()
            self.assertEqual(ip, "198.51.100.42")

    def test_03_path_traversal_prevention_on_file_streaming(self):
        """Verify stream_pdf and stream_video reject path traversal attempts."""
        resp = self.client.get("/stream/pdf/..%2F..%2F..%2Fetc%2Fpasswd")
        self.assertIn(resp.status_code, (400, 404), "Directory traversal in PDF route must be blocked")

        resp = self.client.get("/stream/video/..%2F..%2Fapp.py")
        self.assertIn(resp.status_code, (400, 404), "Directory traversal in video route must be blocked")

    def test_04_csrf_and_origin_validation(self):
        """Verify state-changing POST requests reject disallowed cross-origin callers."""
        resp = self.client.post(
            "/api/appointments",
            headers={"Origin": "https://malicious-attacker-site.com"},
            data=json.dumps({"name": "Test", "phone": "05551112233"}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 403, "Disallowed origin must be rejected with 403")

    def test_05_admin_brute_force_lockout_and_auth(self):
        """Verify admin endpoints lockout IP after repeated failed PIN attempts."""
        attacker_ip = "192.0.2.77"
        
        for i in range(6):
            resp = self.client.get("/api/admin/projects-order", headers={"X-Admin-Pin": "wrong_pin", "CF-Connecting-IP": attacker_ip})
            self.assertEqual(resp.status_code, 403)

        resp = self.client.get("/api/admin/projects-order", headers={"X-Admin-Pin": "wrong_pin", "CF-Connecting-IP": attacker_ip})
        self.assertEqual(resp.status_code, 429, "Brute force lockout must return 429")

    def test_06_appointments_consultant_assignment_and_validation(self):
        """Verify /api/appointments assigns Suzanne Tenekecioğlu as default agent."""
        resp = self.client.post(
            "/api/appointments",
            data=json.dumps({
                "name": "Audit Test User",
                "phone": "0532 999 88 77",
                "project_id": 1,
                "preferred_datetime": "Yarın 15:00",
                "notes": "Automated system test"
            }),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"), "Appointment should succeed")

        conn = sqlite3.connect(str(ROOT_DIR / "nexa_database.db"))
        cur = conn.cursor()
        cur.execute("SELECT assigned_agent, stage FROM customers WHERE phone LIKE '%999 88 77%' ORDER BY id DESC LIMIT 1;")
        row = cur.fetchone()
        self.assertIsNotNone(row, "Customer record must exist")
        self.assertEqual(row[0], "Suzanne Tenekecioğlu", "Default assigned agent must be Suzanne Tenekecioğlu")
        self.assertEqual(row[1], "appointment")
        conn.close()

    def test_07_rag_tool_dispatch_and_sanitization(self):
        """Verify nexa_rag tool functions handle dirty inputs gracefully."""
        import nexa_rag
        
        plan = nexa_rag.calculate_investment_plan("5.000.000 TL", "40%", "24 ay")
        self.assertIn("FİNANSAL HESAPLAMA SONUCU", plan)
        self.assertIn("5.000.000 TL", plan)
        self.assertIn("2.000.000 TL", plan)
        self.assertIn("125.000 TL/ay", plan)

        appt_res = nexa_rag.schedule_vip_appointment(
            customer_name="RAG Function User",
            phone="+90 (535) 123 45 67",
            project_name="ANGİM BEYTEPE",
            preferred_datetime="Pazartesi 14:00"
        )
        self.assertIn("BAŞARILI", appt_res)
        self.assertIn("Suzanne Tenekecioğlu", appt_res)

    def test_08_sales_miner_fuzzy_matching(self):
        """Verify sales miner updates SQLite records correctly."""
        from scripts.nexa_sales_miner import sync_sales_knowledge
        res = sync_sales_knowledge()
        self.assertTrue(res, "Sales miner sync must succeed")

    def test_09_self_healing_cycle(self):
        """Verify full self-healing cycle runs and returns high health score."""
        import nexa_self_healing
        res = nexa_self_healing.run_full_self_healing_cycle()
        self.assertTrue(res.get("passed"), "Self healing must pass")
        self.assertGreaterEqual(res.get("health_score", 0), 90, "Health score must be >= 90%")

    def test_10_ci_sync_pipeline_orchestration(self):
        """Verify CI sync step executor handles return formats."""
        import scripts.ci_sync as ci
        ok, msg = ci.run_step("Self Healing Step", lambda: {"passed": True, "health_score": 98})
        self.assertTrue(ok)
        self.assertIn("OK", msg)

    def test_11_health_and_alias_routes(self):
        """Verify health check routes return healthy JSON."""
        for path in ["/api/health", "/health", "/api/system-status"]:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 200, f"{path} must return 200")
            data = resp.get_json()
            self.assertIn(data.get("status"), ("ok", "healthy"))

    def test_12_chat_greeting_and_persona(self):
        """Verify chat endpoint returns warm natural greeting without intrusive cards for 'merhaba'."""
        resp = self.client.post("/api/nexa-ai-chat", json={"message": "merhaba"})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        response_text = data.get("response", "")
        self.assertIn("Suzanne Tenekecioğlu", response_text)
        self.assertNotIn("Analiz Raporu", response_text)
        self.assertEqual(len(data.get("projects", [])), 0, "Greetings should not return unsolicited project cards")

    def test_13_chat_specific_project_inquiry(self):
        """Verify chat endpoint returns dedicated project info when project is asked."""
        resp = self.client.post("/api/nexa-ai-chat", json={"message": "ANGİM BEYTEPE hakkında bilgi verir misiniz?"})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        response_text = data.get("response", "")
        self.assertIn("ANGİM BEYTEPE", response_text)
        projects = data.get("projects", [])
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["title"], "ANGİM BEYTEPE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
