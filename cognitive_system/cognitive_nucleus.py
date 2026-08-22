# -*- coding: utf-8 -*-
"""
cognitive_nucleus.py — Master Cognitive Reasoning Nucleus (Central Brain)
"""

import json
from datetime import datetime
from typing import Dict, Any
from nexa_autonomous_system import AutonomousCognitiveNucleus, cognitive_nucleus

logger = __import__("logging").getLogger("nexa.cognitive.nucleus")


class CognitiveNucleusWrapper:
    def __init__(self):
        self.nucleus = cognitive_nucleus

    def get_status(self) -> Dict[str, Any]:
        return self.nucleus.get_latest_cognitive_status()

    def step_reasoning(self) -> Dict[str, Any]:
        return self.nucleus.run_single_cognitive_cycle()
