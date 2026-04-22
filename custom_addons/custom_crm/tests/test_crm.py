# -*- coding: utf-8 -*-
"""
===========================================================================
  TEST CRM — Tests E2E pour custom_crm
  Couvre : CrmLead, CrmCompetitor
===========================================================================
"""
from datetime import date, timedelta
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'custom_crm')
class TestCrmLeadCustom(TransactionCase):
    """Tests des champs et actions CRM personnalisés."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client CRM Test',
            'email': 'crm@test.com',
            'phone': '0612345678',
        })
        cls.team = cls.env['crm.team'].search([], limit=1)

    def _create_lead(self, **kwargs):
        vals = {
            'name': 'Opportunité Test',
            'partner_id': self.partner.id,
            'type': 'opportunity',
            'expected_revenue': 25000.0,
        }
        vals.update(kwargs)
        return self.env['crm.lead'].create(vals)

    # ─── Champs personnalisés ────────────────────────────────────────

    def test_01_default_crm_fields(self):
        """Les champs CRM custom ont les bonnes valeurs par défaut."""
        lead = self._create_lead()
        self.assertEqual(lead.call_count, 0)
        self.assertFalse(lead.last_contact_date)
        self.assertFalse(lead.next_action_date)

    def test_02_lead_source_values(self):
        """Toutes les sources de lead sont valides."""
        for src in ('website', 'phone', 'email', 'referral', 'social', 'event', 'advertising', 'other'):
            lead = self._create_lead(lead_source=src, name=f'Lead {src}')
            self.assertEqual(lead.lead_source, src)

    def test_03_lead_quality_values(self):
        """Les qualités de lead sont valides."""
        for q in ('cold', 'warm', 'hot'):
            lead = self._create_lead(lead_quality=q, name=f'Lead {q}')
            self.assertEqual(lead.lead_quality, q)

    def test_04_estimated_closing_date(self):
        """La date de clôture estimée est stockée."""
        d = date.today() + timedelta(days=45)
        lead = self._create_lead(estimated_closing_date=d)
        self.assertEqual(lead.estimated_closing_date, d)

    # ─── Champs calculés ─────────────────────────────────────────────

    def test_10_days_since_last_contact(self):
        """Jours sans contact calculés correctement."""
        lead = self._create_lead(last_contact_date=date.today() - timedelta(days=5))
        self.assertEqual(lead.days_since_last_contact, 5)

    def test_11_days_since_no_contact(self):
        """Sans date de dernier contact → 0 jours."""
        lead = self._create_lead()
        self.assertEqual(lead.days_since_last_contact, 0)

    def test_12_meeting_count_computed(self):
        """Le compteur de RDV est calculé."""
        lead = self._create_lead()
        self.assertIsNotNone(lead.meeting_count_custom)

    def test_13_quote_count_computed(self):
        """Le compteur de devis est calculé."""
        lead = self._create_lead()
        self.assertIsNotNone(lead.quote_count)

    def test_14_conversion_rate_computed(self):
        """Le taux de conversion est calculé."""
        lead = self._create_lead()
        self.assertIsNotNone(lead.conversion_rate)

    # ─── Actions ─────────────────────────────────────────────────────

    def test_20_log_call(self):
        """action_log_call incrémente le compteur et met à jour la date."""
        lead = self._create_lead()
        lead.action_log_call()
        self.assertEqual(lead.call_count, 1)
        self.assertEqual(lead.last_contact_date, date.today())

    def test_21_log_multiple_calls(self):
        """Plusieurs appels incrémentent correctement."""
        lead = self._create_lead()
        lead.action_log_call()
        lead.action_log_call()
        lead.action_log_call()
        self.assertEqual(lead.call_count, 3)

    def test_22_schedule_meeting(self):
        """action_schedule_meeting retourne une action de calendrier."""
        lead = self._create_lead()
        result = lead.action_schedule_meeting()
        self.assertEqual(result.get('type'), 'ir.actions.act_window')
        self.assertEqual(result.get('res_model'), 'calendar.event')

    def test_23_quick_quotation(self):
        """action_quick_quotation crée un devis lié."""
        lead = self._create_lead()
        result = lead.action_quick_quotation()
        self.assertEqual(result.get('type'), 'ir.actions.act_window')
        self.assertEqual(result.get('res_model'), 'sale.order')

    def test_24_view_meetings(self):
        """action_view_meetings retourne une action."""
        lead = self._create_lead()
        result = lead.action_view_meetings()
        self.assertEqual(result.get('type'), 'ir.actions.act_window')

    def test_25_view_quotations(self):
        """action_view_quotations retourne une action."""
        lead = self._create_lead()
        result = lead.action_view_quotations()
        self.assertEqual(result.get('type'), 'ir.actions.act_window')

    def test_26_open_gmail_compose(self):
        """action_open_gmail_compose ouvre Gmail avec un destinataire."""
        lead = self._create_lead()
        result = lead.action_open_gmail_compose()
        self.assertEqual(result.get('type'), 'ir.actions.act_url')
        self.assertIn('mail.google.com', result.get('url', ''))

    def test_27_call_partner(self):
        """action_call_partner ouvre un lien téléphonique."""
        lead = self._create_lead()
        result = lead.action_call_partner()
        self.assertEqual(result.get('type'), 'ir.actions.act_url')
        self.assertTrue(result.get('url', '').startswith('tel:'))

    def test_28_open_whatsapp_chat(self):
        """action_open_whatsapp_chat ouvre une conversation WhatsApp."""
        lead = self._create_lead()
        result = lead.action_open_whatsapp_chat()
        self.assertEqual(result.get('type'), 'ir.actions.act_url')
        self.assertIn('wa.me', result.get('url', ''))

    # ─── Concurrents ─────────────────────────────────────────────────

    def test_30_add_competitor(self):
        """On peut ajouter des concurrents à une opportunité."""
        competitor = self.env['crm.competitor'].create({
            'name': 'Concurrent Alpha',
            'website': 'https://concurrent.com',
            'strength': 'Prix bas',
            'weakness': 'Service client médiocre',
        })
        lead = self._create_lead()
        lead.competitor_ids = [(4, competitor.id)]
        self.assertEqual(len(lead.competitor_ids), 1)

    def test_31_competitor_fields(self):
        """Les champs du concurrent sont stockés."""
        competitor = self.env['crm.competitor'].create({
            'name': 'Concurrent Beta',
            'notes': 'Notes sur le concurrent',
        })
        self.assertTrue(competitor.active)
        self.assertEqual(competitor.name, 'Concurrent Beta')

    # ─── Notes internes ──────────────────────────────────────────────

    def test_35_internal_notes_html(self):
        """Les notes internes HTML sont stockées."""
        lead = self._create_lead(internal_notes='<p>Note stratégique</p>')
        self.assertIn('Note stratégique', lead.internal_notes)

    def test_36_loss_reason_notes(self):
        """Les notes de raison de perte sont stockées."""
        lead = self._create_lead(loss_reason_notes='Client a choisi le concurrent sur le prix')
        self.assertEqual(lead.loss_reason_notes, 'Client a choisi le concurrent sur le prix')
