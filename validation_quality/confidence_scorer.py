# -*- coding: utf-8 -*-
"""
confidence_scorer.py — Extracted Data Field Confidence Scoring
"""

from typing import Dict, Any


class ConfidenceScorer:
    @staticmethod
    def score_field(field_name: str, value: Any) -> float:
        if value is None or str(value).strip() == "":
            return 0.0
        val_str = str(value).strip()
        if field_name == "phone":
            return 95.0 if len(val_str) >= 10 else 40.0
        if field_name == "price":
            return 95.0 if val_str.isdigit() or "TL" in val_str else 60.0
        if field_name in ("ada_no", "parsel_no"):
            return 98.0 if val_str.isdigit() else 75.0
        return 90.0
