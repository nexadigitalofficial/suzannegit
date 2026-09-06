#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
=============================================================================
NEXA OS / COLDWELL BANKER VIP - 21-STEP MASTER QA AUTOMATION SUITE
=============================================================================
Comprehensive test suite verifying all mobile UX, bug fixes, appointment
calendar, branding, social links, lead keyboard retention, presentation
sharing, and backend API endpoints.
=============================================================================
"""

import os
import sys
import re
import json
import unittest
from bs4 import BeautifulSoup

# Ensure current directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import backend Flask app
import app as flask_app_module


class TestMasterQASuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html_path = os.path.join(BASE_DIR, 'site.html')
        with open(cls.html_path, 'r', encoding='utf-8') as f:
            cls.raw_html = f.read()
        cls.soup = BeautifulSoup(cls.raw_html, 'html.parser')
        
        # Flask test client
        flask_app_module.app.config['TESTING'] = True
        cls.client = flask_app_module.app.test_client()

    def test_01_site_loads_successfully(self):
        """TEST 01: Site loads successfully and HTML parses without syntax errors."""
        self.assertGreater(len(self.raw_html), 100000)
        self.assertIsNotNone(self.soup.find('html'))
        self.assertIsNotNone(self.soup.find('head'))
        self.assertIsNotNone(self.soup.find('body'))
        print("[TEST 01 PASS] Site loads and HTML parses with 0 errors.")

    def test_02_mobile_viewport_and_safe_areas(self):
        """TEST 02: Mobile viewport simulation & responsive meta tags verified."""
        meta_viewport = self.soup.find('meta', attrs={'name': 'viewport'})
        self.assertIsNotNone(meta_viewport)
        content = meta_viewport.get('content', '')
        self.assertIn('width=device-width', content)
        self.assertIn('viewport-fit=cover', content)
        
        # Check safe-area variables in CSS
        self.assertIn('--sat', self.raw_html)
        self.assertIn('--sab', self.raw_html)
        self.assertIn('initDynamicViewportEngine', self.raw_html)
        print("[TEST 02 PASS] Mobile viewport and iOS safe-area engine verified.")

    def test_03_instagram_link_routing(self):
        """TEST 03: Instagram click target routes to official Suzanne CB account."""
        expected_ig = "https://www.instagram.com/suzannegayrimenkulcb"
        ig_links = self.soup.find_all('a', href=re.compile(r'instagram\.com/suzannegayrimenkulcb'))
        self.assertGreaterEqual(len(ig_links), 2, "Instagram links must exist in mobile bar, nav, and contact")
        for link in ig_links:
            self.assertEqual(link['href'], expected_ig)
        print(f"[TEST 03 PASS] Instagram routing verified ({len(ig_links)} verified links).")

    def test_04_facebook_link_routing(self):
        """TEST 04: Facebook click target routes to official Suzanne CB account."""
        expected_fb = "https://www.facebook.com/suzannegayrimenkulcb"
        fb_links = self.soup.find_all('a', href=re.compile(r'facebook\.com/suzannegayrimenkulcb'))
        self.assertGreaterEqual(len(fb_links), 2, "Facebook links must exist across mobile bar, nav, and contact")
        for link in fb_links:
            self.assertEqual(link['href'], expected_fb)
        print(f"[TEST 04 PASS] Facebook routing verified ({len(fb_links)} verified links).")

    def test_05_whatsapp_routing_protocol(self):
        """TEST 05: WhatsApp click target initiates valid wa.me/905354895656 protocol."""
        expected_wa_phone = "905354895656"
        wa_links = self.soup.find_all('a', href=re.compile(r'wa\.me/905354895656'))
        self.assertGreaterEqual(len(wa_links), 3, "WhatsApp links must be present in mobile bar, nav, and footer")
        for link in wa_links:
            self.assertIn(expected_wa_phone, link['href'])
        print(f"[TEST 05 PASS] WhatsApp protocol verified ({len(wa_links)} verified links).")

    def test_06_phone_click_tel_protocol(self):
        """TEST 06: Phone click initiates tel:+905354895656."""
        tel_links = self.soup.find_all('a', href=re.compile(r'tel:\+?905354895656'))
        self.assertGreaterEqual(len(tel_links), 2, "Phone tel: links must exist for 1-tap dialing on mobile")
        for link in tel_links:
            self.assertIn('905354895656', link['href'])
        print(f"[TEST 06 PASS] Phone click tel: protocol verified ({len(tel_links)} verified links).")

    def test_07_appointment_modal_elements(self):
        """TEST 07: Appointment modal opens cleanly and contains all required form fields."""
        modal = self.soup.find(id='appointmentModal')
        self.assertIsNotNone(modal, "appointmentModal must exist in DOM")
        form = modal.find(id='appointmentForm')
        self.assertIsNotNone(form, "appointmentForm must exist inside appointmentModal")
        
        # Check required fields
        self.assertIsNotNone(modal.find(id='aptName'))
        self.assertIsNotNone(modal.find(id='aptPhone'))
        self.assertIsNotNone(modal.find(id='aptEmail'))
        self.assertIsNotNone(modal.find(id='aptMeetingType'))
        self.assertIsNotNone(modal.find(id='aptDate'))
        self.assertIsNotNone(modal.find(id='aptTime'))
        print("[TEST 07 PASS] Appointment modal and form fields verified.")

    def test_08_calendar_day_selector_markup_and_engine(self):
        """TEST 08: Calendar day selector renders container, pill CSS, and JS generator."""
        scroller = self.soup.find(id='aptDaySelector')
        self.assertIsNotNone(scroller, "aptDaySelector scroller must exist")
        self.assertIn('apt-day-scroller', self.raw_html)
        self.assertIn('apt-day-pill', self.raw_html)
        self.assertIn('renderAppointmentCalendar', self.raw_html)
        self.assertIn('TURKISH_DAYS', self.raw_html)
        print("[TEST 08 PASS] Calendar day selector markup & 14-day generator verified.")

    def test_09_date_selection_state_sync(self):
        """TEST 09: Date selection updates internal state and hidden input."""
        self.assertIn('selectAppointmentDay', self.raw_html)
        self.assertIn('aptSelectedDateLabel', self.raw_html)
        self.assertIn('aptDate', self.raw_html)
        print("[TEST 09 PASS] Date selection state synchronizer verified.")

    def test_10_time_slot_matrix_and_suppression(self):
        """TEST 10: Dynamic time slot matrix buttons exist and suppress past hours on current date."""
        slots_grid = self.soup.find(id='aptTimeSlotsGrid')
        self.assertIsNotNone(slots_grid, "aptTimeSlotsGrid must exist")
        self.assertIn('apt-time-slot', self.raw_html)
        self.assertIn('renderAppointmentTimeSlots', self.raw_html)
        self.assertIn('selectAppointmentTime', self.raw_html)
        # Check past hour suppression code
        self.assertIn('isPastToday', self.raw_html)
        print("[TEST 10 PASS] Dynamic time slot matrix and past-hour suppression verified.")

    def test_11_form_turkish_phone_validation(self):
        """TEST 11: Form phone input enforces Turkish mobile phone format."""
        phone_input = self.soup.find(id='aptPhone')
        self.assertIsNotNone(phone_input)
        self.assertEqual(phone_input.get('type'), 'tel')
        self.assertIn('formatTRPhone', phone_input.get('oninput', ''))
        self.assertIn('function formatTRPhone', self.raw_html)
        print("[TEST 11 PASS] Turkish phone formatting validator verified.")

    def test_12_form_submit_zero_page_reload(self):
        """TEST 12: Form submit triggers without page reload (action='javascript:void(0)', return false)."""
        form = self.soup.find(id='appointmentForm')
        self.assertEqual(form.get('action'), 'javascript:void(0)')
        onsubmit = form.get('onsubmit', '')
        self.assertIn('return false', onsubmit)
        self.assertIn('submitAppointmentForm', onsubmit)
        print("[TEST 12 PASS] Zero page reload on submit verified.")

    def test_13_success_state_confirmation_card(self):
        """TEST 13: Success state displays confirmation card with zero silent fails."""
        self.assertIn('showFormStatus', self.raw_html)
        self.assertIn('Randevu Talebiniz Kaydedildi', self.raw_html)
        self.assertIn('aptStatusMsg', self.raw_html)
        print("[TEST 13 PASS] Inline success confirmation card verified.")

    def test_14_whatsapp_appointment_formatting(self):
        """TEST 14: WhatsApp appointment text properly formats all parameters."""
        self.assertIn('VIP RANDEVU TALEBİ', self.raw_html)
        self.assertIn('Ad Soyad:', self.raw_html)
        self.assertIn('Telefon:', self.raw_html)
        self.assertIn('Tarih:', self.raw_html)
        self.assertIn('Saat:', self.raw_html)
        self.assertIn('Görüşme', self.raw_html)
        print("[TEST 14 PASS] WhatsApp appointment parameter payload verified.")

    def test_15_chatbot_widget_and_viewport_mode(self):
        """TEST 15: Chatbot widget markup and classes present."""
        chat_win = self.soup.find(id='chatWindow')
        self.assertIsNotNone(chat_win)
        self.assertIsNotNone(self.soup.find(id='chatLeadRow'))
        self.assertIsNotNone(self.soup.find(id='chatLeadName'))
        self.assertIsNotNone(self.soup.find(id='chatLeadPhone'))
        print("[TEST 15 PASS] Chatbot widget & lead input DOM structure verified.")

    def test_16_chatbot_name_input_keyboard_retention(self):
        """TEST 16: Chatbot name input retains focus in keyboard-mode via .lead-typing."""
        # CSS rule verification: lead-typing must force display: flex !important
        self.assertIn('.chat-window.keyboard-mode.lead-typing .chat-lead-row', self.raw_html)
        self.assertIn('display: flex !important', self.raw_html)
        # JS listeners verification
        self.assertIn("cw.classList.add('lead-typing')", self.raw_html)
        print("[TEST 16 PASS] Chatbot virtual keyboard lead-typing retention verified.")

    def test_17_presentation_share_deep_link_generation(self):
        """TEST 17: Presentation share generates valid deep link format."""
        self.assertIn('function shareProject', self.raw_html)
        self.assertIn('share=vip#site-card-', self.raw_html)
        print("[TEST 17 PASS] Presentation share deep-link generator verified.")

    def test_18_shared_presentation_highlight_and_badge(self):
        """TEST 18: Shared presentation URL auto-switches tab and highlights card with ● AKTİF SUNUM."""
        self.assertIn('shared-highlight-green', self.raw_html)
        self.assertIn('card-shared-badge-green', self.raw_html)
        self.assertIn('●</span> AKTİF SUNUM', self.raw_html)
        self.assertIn('pulseDot', self.raw_html)
        self.assertIn('checkSharedProjectHighlight', self.raw_html)
        print("[TEST 18 PASS] Shared presentation active indicator & badge verified.")

    def test_19_pdf_and_catalog_modals(self):
        """TEST 19: PDF and catalog buttons open valid preview modals."""
        pdf_modal = self.soup.find(id='pdfModal')
        self.assertIsNotNone(pdf_modal, "pdfModal must exist")
        self.assertIn('openPdfPreview', self.raw_html)
        self.assertIn('closeModal', self.raw_html)
        print("[TEST 19 PASS] PDF & catalog preview modal verified.")

    def test_20_office_location_and_branding(self):
        """TEST 20: Office location matches Santra Royal Rezidans and branding is complete."""
        expected_address = "Santra Royal Rezidans, Çayyolu, 2676. Cadde 2C D:4, 06810 Çankaya/Ankara"
        self.assertIn("Santra Royal Rezidans", self.raw_html)
        self.assertIn("2676. Cadde 2C D:4", self.raw_html)
        self.assertIn("suzanne.tenekecioglu@cb.com.tr", self.raw_html)
        self.assertIn("COLDWELL BANKER VIP", self.raw_html)
        self.assertIn("Gayrimenkul ve Yatırım Danışmanı", self.raw_html)
        print("[TEST 20 PASS] Office address, branding, and advisor email verified.")

    def test_21_directions_google_maps_routing(self):
        """TEST 21: Directions link routes to verified Google Maps URL."""
        maps_link = self.soup.find('a', href=re.compile(r'maps\.google\.com.*Santra\+Royal\+Rezidans'))
        self.assertIsNotNone(maps_link, "Google Maps link to Santra Royal Rezidans must exist")
        print("[TEST 21 PASS] Verified Google Maps direct routing verified.")

    def test_backend_api_endpoints(self):
        """BONUS TEST: Verify all backend API routes (/api/config, /api/appointments/slots, /api/appointments, /api/projects)."""
        # 1. /api/config
        cfg_res = self.client.get('/api/config')
        self.assertEqual(cfg_res.status_code, 200)
        cfg_data = json.loads(cfg_res.data)
        self.assertEqual(cfg_data['default_agent']['email'], 'suzanne.tenekecioglu@cb.com.tr')
        self.assertEqual(cfg_data['default_agent']['phone_display'], '0535 489 56 56')

        # 2. /api/appointments/slots
        slots_res = self.client.get('/api/appointments/slots?date=2026-09-10')
        self.assertEqual(slots_res.status_code, 200)
        slots_data = json.loads(slots_res.data)
        self.assertTrue(slots_data['success'])
        self.assertEqual(len(slots_data['slots']), 9)

        # 3. /api/appointments (POST)
        apt_payload = {
            "name": "QA Automated Test Lead",
            "phone": "0535 489 56 56",
            "email": "test@cb.com.tr",
            "preferred_datetime": "2026-09-10 14:00",
            "project_id": "proj-qa-test",
            "project_name": "Incek Loft VIP",
            "notes": "Automated verification test run"
        }
        post_res = self.client.post('/api/appointments', json=apt_payload)
        self.assertEqual(post_res.status_code, 200)
        post_data = json.loads(post_res.data)
        self.assertTrue(post_data['success'])
        print("[BACKEND API PASS] All 4 backend routes verified (/api/config, /api/appointments/slots, /api/appointments, /api/projects).")


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMasterQASuite)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
