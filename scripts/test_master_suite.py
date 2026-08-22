# -*- coding: utf-8 -*-
"""
test_master_suite.py — Master Enterprise Test Suite for NEXA PRIME v2
Validates Drive Integration, Multi-Layer Validation, Cognitive Swarm, Scheduling & Monitoring.
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Import modular packages
from drive_integration.gdrive_auth_manager import GoogleAuthenticator, CredentialManager, AuthAuditLogger
from drive_integration.gdrive_file_discovery import DriveFileDiscovery, DuplicateDetector
from drive_integration.intelligent_extraction_engine import ExtractionEngine
from drive_integration.sync_engine import SyncOrchestrator

from validation_quality.validation_engine import ValidationEngine
from validation_quality.deduplication_engine import DeduplicationEngine
from validation_quality.confidence_scorer import ConfidenceScorer
from validation_quality.tkgm_verifier import TKGMVerifier

from cognitive_system.cognitive_nucleus import CognitiveNucleusWrapper
from cognitive_system.agent_orchestration import AgentSwarmCoordinator
from cognitive_system.predictive_intelligence import PredictiveIntelligenceWrapper
from cognitive_system.learning_engine import ContinuousLearningWrapper

from automation.intelligent_scheduler import AdaptiveScheduler
from monitoring.metrics_aggregator import MetricsAggregator
from monitoring.alert_manager import AlertManager
from monitoring.cognitive_dashboard import CognitiveDashboardService


class TestNexaEnterpriseMasterSuite(unittest.TestCase):

    # 1. Drive Integration Tests
    def test_01_drive_auth_and_rotation(self):
        auth = GoogleAuthenticator()
        self.assertTrue(auth.authenticate())
        self.assertTrue(auth.refresh_token_if_needed())
        cred = CredentialManager()
        k1 = cred.get_active_key()
        k2 = cred.rotate_key()
        self.assertNotEqual(k1, k2)
        evt = AuthAuditLogger.log_auth_event("test_auth", True)
        self.assertTrue(evt["success"])

    def test_02_drive_discovery_and_extraction(self):
        disc = DriveFileDiscovery()
        files = disc.discover_all_files()
        self.assertIsInstance(files, list)

        ext_engine = ExtractionEngine()
        # Test text extraction from existing JSON file
        kg_path = BASE_DIR / "nexa_sales_knowledge_graph.json"
        if kg_path.exists():
            res = ext_engine.extract_from_file(kg_path)
            self.assertTrue(res["success"])
            self.assertGreater(res["confidence"], 80.0)

    def test_03_sync_engine_execution(self):
        sync = SyncOrchestrator()
        inc_res = sync.perform_incremental_sync()
        self.assertIn(inc_res["status"], ["success", "skipped"])

    # 2. Validation & Quality Tests
    def test_04_validation_engine_layers(self):
        val = ValidationEngine()
        valid_proj = {
            "name": "TEST RESIDENCE",
            "price_min": 2000000,
            "price_max": 4000000,
            "ada_no": "123",
            "parsel_no": "4"
        }
        res = val.validate_project_record(valid_proj)
        self.assertTrue(res["valid"])
        self.assertEqual(res["confidence_score"], 100.0)

        invalid_proj = {
            "name": "TEST INVALID",
            "price_min": 5000000,
            "price_max": 3000000  # min > max
        }
        res_inv = val.validate_project_record(invalid_proj)
        self.assertFalse(res_inv["valid"])

    def test_05_deduplication_and_confidence(self):
        dedup = DeduplicationEngine()
        customers = [
            {"name": "Ahmet Yılmaz", "phone": "0532 111 22 33"},
            {"name": "Ahmet Y.", "phone": "+90 532 111 22 33"}
        ]
        dups = dedup.find_duplicate_customers(customers)
        self.assertEqual(len(dups), 1)

        scorer = ConfidenceScorer()
        self.assertEqual(scorer.score_field("phone", "05354895656"), 95.0)
        self.assertEqual(scorer.score_field("ada_no", "96400"), 98.0)

    def test_06_tkgm_verifier(self):
        tkgm = TKGMVerifier()
        res = tkgm.verify_parcel("Ankara", "Pursaklar", "Saray", "96400", "6")
        self.assertTrue(res["verified"])
        self.assertEqual(res["confidence"], 99.5)

    # 3. Cognitive & Swarm Tests
    def test_07_cognitive_nucleus_and_swarm(self):
        nucleus = CognitiveNucleusWrapper()
        status = nucleus.get_status()
        self.assertIn("health_score", status)

        swarm = AgentSwarmCoordinator()
        swarm_res = swarm.dispatch_all({"total_projects": 31, "projects_with_docs": 31})
        self.assertIn("orchestrator", swarm_res)
        self.assertIn("anomalies", swarm_res)
        self.assertIn("guardian", swarm_res)

    def test_08_predictive_and_learning_engines(self):
        pred = PredictiveIntelligenceWrapper()
        forecast = pred.forecast_24h({"error_rate": 0.0})
        self.assertEqual(forecast["forecast_window"], "24h")

        learn = ContinuousLearningWrapper()
        lessons = learn.learn({"status": "optimal"})
        self.assertGreaterEqual(lessons["lessons_learned_count"], 1)

    # 4. Automation & Monitoring Tests
    def test_09_adaptive_scheduler_circuit_breaker(self):
        scheduler = AdaptiveScheduler()
        res = scheduler.execute_with_circuit_breaker("dummy_task", lambda: 42)
        self.assertTrue(res["success"])
        self.assertEqual(res["result"], 42)

    def test_10_monitoring_and_dashboard(self):
        metrics = MetricsAggregator.collect_all_metrics()
        self.assertIn("total_projects", metrics)

        alerts = AlertManager()
        alert = alerts.dispatch_alert("INFO", "Sistem nominal", {"load": "normal"})
        self.assertEqual(alert["severity"], "INFO")

        dash = CognitiveDashboardService.get_live_stream()
        self.assertEqual(dash["version"], "2.0-Autonomous")
        self.assertTrue(dash["cognitive_nucleus"]["reasoning_active"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
