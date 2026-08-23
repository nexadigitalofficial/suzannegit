#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEXA PRIME v2 — ULTRA KAPSAMLI CHATBOT VE DIYALOG STRES TESTI
Tum gercek musteri senaryolarini, tekil proje sorgularini, teslim tarihlerini,
odeme planlarini, tapu/TKGM sorgularini ve cok turlu diyaloglari dogrular.
"""

import unittest
import sys
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import app
from nexa_ai_engine import process_nexa_query, extract_keywords_and_projects
from nexa_rag import cognitive_chat, _find_project_by_name


class TestChatbotAdvancedStress(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        app.config["TESTING"] = True

    def test_01_evart_yalikavak_delivery_date(self):
        """Kullanici: 'evart yalikavak teslimat tarihi' -> 12 ay / teslim tarihi net verilmeli."""
        queries = [
            "evart yalikavak teslimat tarihi",
            "evarty yalikavak teslim",
            "evart yalikavak ne zaman teslim edilir",
            "bodrum yalikavak teslim suresi kac ay"
        ]
        for q in queries:
            res = process_nexa_query(q)
            text = res.get("response", "")
            self.assertTrue(res.get("success"), f"Query failed: {q}")
            self.assertIn("12 Ay", text, f"Expected '12 Ay' in response for '{q}': {text}")
            self.assertIn("EVART YALIKAVAK", text)
            self.assertTrue(len(res.get("projects", [])) >= 1)

    def test_02_angim_beytepe_delivery_and_installments(self):
        """Kullanici: 'angim beytepe teslim tarihi ve taksitleri' -> 48 ay teslim, 24-36 ay taksit."""
        res = process_nexa_query("angim beytepe teslim tarihi ve taksitleri")
        text = res.get("response", "")
        self.assertTrue(res.get("success"))
        self.assertIn("ANGİM BEYTEPE", text)
        self.assertTrue("48 Ay" in text or "48" in text)
        self.assertTrue("Taksit" in text or "Peşinat" in text)

    def test_03_joven_kampus_student_rental_investment(self):
        """Kullanici: 'joven kampus ogrenci kira getirisi var mi' -> Yatirim odakli yanit."""
        res = process_nexa_query("joven kampus ogrenci kira getirisi var mi")
        text = res.get("response", "")
        self.assertTrue(res.get("success"))
        self.assertIn("JOVEN KAMPÜS", text)
        self.assertTrue("Yatırım" in text or "Kira" in text or "Kampüs" in text)
        self.assertTrue(len(res.get("projects", [])) >= 1)

    def test_04_vip_marin_alanya_features_and_summer(self):
        """Kullanici: 'yazlik var mi' veya 'vip marin alanya ozellikleri' -> Alanya ve Bodrum projeleri."""
        res = process_nexa_query("yazlik var mi")
        text = res.get("response", "")
        self.assertTrue(res.get("success"))
        project_titles = [p.get("title") for p in res.get("projects", [])]
        self.assertTrue(any("MARIN" in t or "YALIKAVAK" in t or "İNCEK" in t for t in project_titles))

    def test_05_s_point_saray_ada_parsel_and_zero_down_payment(self):
        """Kullanici: 's point vip saray pesinatsiz taksit var mi' -> %0 pesinatsiz taksit ve Ada 96400/6."""
        res = process_nexa_query("s point vip saray pesinatsiz taksit var mi")
        text = res.get("response", "")
        self.assertTrue(res.get("success"))
        self.assertIn("S POINT - VIP SARAY", text)
        self.assertTrue("Peşinatsız" in text or "%0" in text or "55.270" in text)
        self.assertTrue("96400" in text)

    def test_06_pure_greetings_no_unsolicited_cards(self):
        """Kullanici: 'merhaba', 'selamlar', 'iyi gunler' -> Tanitim mesaji, projects kartlari bos olmali."""
        for g in ["merhaba", "selam", "gunaydin", "iyi gunler", "selamlar!"]:
            res = process_nexa_query(g)
            self.assertTrue(res.get("success"))
            self.assertIn("Suzanne Tenekecioğlu", res.get("response", ""))
            self.assertEqual(len(res.get("projects", [])), 0, f"Greeting '{g}' should return 0 cards")

    def test_07_appointment_and_phone_inquiry(self):
        """Kullanici: 'randevu almak istiyorum' -> VIP randevu kanallari ve telefon 0535 489 56 56."""
        res = process_nexa_query("randevu almak istiyorum")
        text = res.get("response", "")
        self.assertTrue(res.get("success"))
        self.assertIn("0535 489 56 56", text)
        self.assertEqual(res.get("lead_score"), 9)

    def test_08_api_chat_endpoint_multi_scenario_stress(self):
        """POST /api/chat ve /api/nexa-ai-chat uc noktalarini 10 farkli gercek sorguyla stres testine tabi tutar."""
        scenarios = [
            {"msg": "merhaba", "check": "Suzanne Tenekecioğlu"},
            {"msg": "evart yalikavak teslimat tarihi", "check": "12 Ay"},
            {"msg": "angim beytepe fiyati nedir", "check": "6.350.000"},
            {"msg": "vip universite ada parsel nedir", "check": "190438"},
            {"msg": "5-10M yatirim icin luks proje", "check": "TL"},
            {"msg": "yazlik villa secenekleri", "check": "YALIKAVAK"},
            {"msg": "randevu almak istiyorum", "check": "0535 489 56 56"},
            {"msg": "cankaya luks konut ilanlari", "check": "Çankaya"},
            {"msg": "grande yasamkent kac ayda teslim", "check": "Yaşamkent"},
            {"msg": "s point pursaklar odeme plani", "check": "S POINT"},
        ]
        for sc in scenarios:
            resp = self.client.post(
                "/api/chat",
                data=json.dumps({"message": sc["msg"], "history": []}),
                content_type="application/json"
            )
            self.assertEqual(resp.status_code, 200, f"Failed on query: {sc['msg']}")
            data = resp.get_json()
            self.assertTrue(data.get("success"))
            r_text = data.get("response", "")
            self.assertTrue(len(r_text) > 30, f"Response too short for {sc['msg']}: {r_text}")
            self.assertIn(sc["check"].lower(), r_text.lower(), f"Expected '{sc['check']}' in response for '{sc['msg']}':\n{r_text}")

    def test_09_all_31_projects_have_delivery_and_pricing(self):
        """Tum 31 projenin veritabaninda ve Knowledge Graph'ta fiyat, pesinat, taksit ve teslim suresi dogrulugu."""
        prices_file = ROOT / "nexa_project_prices.json"
        self.assertTrue(prices_file.exists())
        prices = json.loads(prices_file.read_text(encoding="utf-8"))
        self.assertTrue(len(prices) >= 30)

        for name, p in prices.items():
            self.assertIsNotNone(p.get("price_display"), f"{name} missing price_display")
            self.assertIsNotNone(p.get("down_payment"), f"{name} missing down_payment")
            self.assertIsNotNone(p.get("installment_terms"), f"{name} missing installment_terms")
            self.assertIsNotNone(p.get("delivery_months"), f"{name} missing delivery_months")
            self.assertTrue(p.get("delivery_months") > 0, f"{name} delivery_months must be > 0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
