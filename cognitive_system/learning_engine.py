# -*- coding: utf-8 -*-
"""
learning_engine.py — Continuous Learning and Dynamic Rule Extraction Engine
"""

from typing import Dict, Any
from nexa_autonomous_system import ContinuousLearningEngine


class ContinuousLearningWrapper:
    def __init__(self):
        self.engine = ContinuousLearningEngine()

    def learn(self, operation_results: Dict[str, Any]) -> Dict[str, Any]:
        return self.engine.extract_lessons(operation_results)
