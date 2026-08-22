# -*- coding: utf-8 -*-
"""
predictive_intelligence.py — 24-Hour Failure & Bottleneck Forecasting Engine
"""

from typing import Dict, Any
from nexa_autonomous_system import PredictiveIntelligenceEngine


class PredictiveIntelligenceWrapper:
    def __init__(self):
        self.engine = PredictiveIntelligenceEngine()

    def forecast_24h(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        return self.engine.predict_future_issues(metrics)
