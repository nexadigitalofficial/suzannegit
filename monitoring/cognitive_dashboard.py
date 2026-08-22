# -*- coding: utf-8 -*-
"""
cognitive_dashboard.py — Real-Time Streaming Cognitive Dashboard Service
"""

from typing import Dict, Any
from nexa_autonomous_system import CognitiveMonitoringDashboard


class CognitiveDashboardService:
    @staticmethod
    def get_live_stream() -> Dict[str, Any]:
        return CognitiveMonitoringDashboard.get_dashboard_data()
