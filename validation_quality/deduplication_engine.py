# -*- coding: utf-8 -*-
"""
deduplication_engine.py — Customer and Lead Deduplication Engine
"""

import re
from typing import List, Dict, Any


class DeduplicationEngine:
    @staticmethod
    def normalize_phone(phone: str) -> str:
        digits = re.sub(r"\D", "", phone or "")
        if digits.startswith("90") and len(digits) == 12:
            digits = digits[2:]
        if digits.startswith("0") and len(digits) == 11:
            digits = digits[1:]
        return digits

    def find_duplicate_customers(self, customers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen_phones = {}
        duplicates = []
        for c in customers:
            norm_p = self.normalize_phone(c.get("phone", ""))
            if not norm_p:
                continue
            if norm_p in seen_phones:
                duplicates.append({
                    "original": seen_phones[norm_p],
                    "duplicate": c,
                    "matched_phone": norm_p
                })
            else:
                seen_phones[norm_p] = c
        return duplicates
