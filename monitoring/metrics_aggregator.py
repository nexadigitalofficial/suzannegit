# -*- coding: utf-8 -*-
"""
metrics_aggregator.py — System Health, Vector DB and Lead Telemetry Aggregator
"""

from typing import Dict, Any
from nexa_autonomous_system import cognitive_nucleus


class MetricsAggregator:
    @staticmethod
    def collect_all_metrics() -> Dict[str, Any]:
        return cognitive_nucleus.analyze_current_state()
