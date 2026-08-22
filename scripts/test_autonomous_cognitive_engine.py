# -*- coding: utf-8 -*-
"""
test_autonomous_cognitive_engine.py — Comprehensive Test Suite for Autonomous Cognitive Nucleus
Tests all 5 Agent Swarm Tiers, Predictive Intelligence, Continuous Learning, and Real-Time Dashboard.
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from nexa_autonomous_system import (
    AutonomousCognitiveNucleus,
    MasterOrchestrator,
    AnomalyScout,
    AdaptiveDiscoveryAgent,
    DiagnosticGuardian,
    QuantumPerformanceOptimizer,
    PredictiveIntelligenceEngine,
    ContinuousLearningEngine,
    CognitiveMonitoringDashboard,
    cognitive_nucleus
)
import app


class TestAutonomousCognitiveEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.app.test_client()

    def test_01_master_orchestrator_tier1(self):
        """Verify Tier 1 Master Orchestrator generates coordinated task assignments."""
        orchestrator = MasterOrchestrator()
        state = {
            "missing_documents_count": 2,
            "drive_pending_files": 3,
            "orphan_chunks_detected": 1
        }
        res = orchestrator.coordinate(state)
        self.assertEqual(res["status"], "coordinated")
        self.assertEqual(res["active_tasks_count"], 3)
        actions = [t["action"] for t in res["tasks"]]
        self.assertIn("hydrate_missing_documents", actions)
        self.assertIn("pull_drive_updates", actions)
        self.assertIn("cleanup_orphans", actions)

    def test_02_anomaly_scout_tier2(self):
        """Verify Tier 2 Anomaly Scout identifies coverage gaps and zero chunks."""
        scout = AnomalyScout()
        anomalies = scout.detect_anomalies({"total_projects": 31, "projects_with_docs": 28})
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["type"], "COVERAGE_GAP")

        anomalies_zero = scout.detect_anomalies({"total_docs": 100, "total_chunks": 0})
        self.assertEqual(len(anomalies_zero), 1)
        self.assertEqual(anomalies_zero[0]["type"], "ZERO_CHUNKS")

    def test_03_adaptive_discovery_tier3(self):
        """Verify Tier 3 Adaptive Discovery discovers multi-format files and Drive state."""
        discovery = AdaptiveDiscoveryAgent()
        res = discovery.discover_local_and_drive()
        self.assertEqual(res["status"], "synced")
        self.assertIn(".pdf", res["supported_formats"])
        self.assertIn(".xlsx", res["supported_formats"])
        self.assertIn(".docx", res["supported_formats"])
        self.assertIn(".txt", res["supported_formats"])
        self.assertGreaterEqual(res["drive_tracked_count"], 0)

    def test_04_diagnostic_guardian_tier4(self):
        """Verify Tier 4 Diagnostic Guardian heals database integrity."""
        guardian = DiagnosticGuardian()
        res = guardian.diagnose_and_heal()
        self.assertEqual(res["status"], "healthy")
        self.assertIn("fixes_applied", res)

    def test_05_quantum_optimizer_tier5(self):
        """Verify Tier 5 Quantum Performance Optimizer runs database optimization."""
        optimizer = QuantumPerformanceOptimizer()
        res = optimizer.optimize()
        self.assertEqual(res["status"], "optimized")
        self.assertIn("optimizations", res)

    def test_06_predictive_intelligence_engine(self):
        """Verify Predictive Intelligence Engine calculates risk score and forecast."""
        predictive = PredictiveIntelligenceEngine()
        res = predictive.predict_future_issues({"error_rate": 0.01})
        self.assertEqual(res["forecast_window"], "24h")
        self.assertLessEqual(res["system_risk_score"], 0.10)
        self.assertGreaterEqual(len(res["potential_issues"]), 1)

    def test_07_continuous_learning_engine(self):
        """Verify Continuous Learning Engine extracts operational lessons."""
        learning = ContinuousLearningEngine()
        res = learning.extract_lessons({"state": "success"})
        self.assertGreaterEqual(res["lessons_learned_count"], 1)
        self.assertEqual(res["learning_health_score"], 100)

    def test_08_autonomous_cognitive_nucleus_cycle(self):
        """Verify Central Autonomous Cognitive Nucleus runs a complete reasoning cycle."""
        nucleus = AutonomousCognitiveNucleus()
        cycle = nucleus.run_single_cognitive_cycle()
        self.assertIn(cycle["status"], ["OPTIMAL", "HEALTHY"])
        self.assertGreaterEqual(cycle["health_score"], 90.0)
        self.assertIn("state", cycle)
        self.assertIn("predictions", cycle)
        self.assertIn("coordination", cycle)
        self.assertIn("guardian", cycle)

    def test_09_cognitive_monitoring_api_endpoint(self):
        """Verify /api/cognitive/status returns real-time cognitive dashboard data."""
        resp = self.client.get("/api/cognitive/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        c_data = data.get("data", {})
        self.assertEqual(c_data.get("system_name"), "NEXA PRIME v2 Autonomous Cognitive System")
        self.assertTrue(c_data.get("cognitive_nucleus", {}).get("reasoning_active"))
        self.assertEqual(c_data.get("tier_swarm_status", {}).get("tier_1_orchestrators"), "ACTIVE")
        self.assertEqual(c_data.get("tier_swarm_status", {}).get("tier_4_guardians"), "ACTIVE")
        self.assertTrue(c_data.get("data_layer", {}).get("zero_hallucination_lock"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
