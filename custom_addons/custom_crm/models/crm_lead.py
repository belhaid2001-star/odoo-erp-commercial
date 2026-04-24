# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from urllib.parse import quote


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # --- Champs personnalisés ---
    lead_source = fields.Selection([
        ('website', 'Site web'),
        ('phone', 'Téléphone'),
        ('email', 'Email'),
        ('referral', 'Recommandation'),
        ('social', 'Réseaux sociaux'),
        ('event', 'Événement'),
        ('advertising', 'Publicité'),
        ('other', 'Autre'),
    ], string='Source de la piste', tracking=True)

    lead_quality = fields.Selection([
        ('cold', 'Froid'),
        ('warm', 'Tiède'),
        ('hot', 'Chaud'),
    ], string='Qualité de la piste', tracking=True,
       compute='_compute_lead_quality', store=True, readonly=False)

    estimated_closing_date = fields.Date(
        string='Date de clôture estimée',
        tracking=True,
    )

    competitor_ids = fields.Many2many(
        'crm.competitor',
        string='Concurrents',
    )

    loss_reason_notes = fields.Text(
        string='Notes de perte',
    )

    next_action_description = fields.Text(
        string='Prochaine action',
    )

    next_action_date = fields.Date(
        string='Date prochaine action',
        tracking=True,
    )

    call_count = fields.Integer(
        string='Nombre d\'appels',
        default=0,
    )

    meeting_count_custom = fields.Integer(
        string='Nombre de RDV',
        compute='_compute_meeting_count_custom',
    )

    quote_count = fields.Integer(
        string='Nombre de devis',
        compute='_compute_quote_count',
    )

    conversion_rate = fields.Float(
        string='Probabilité pondérée',
        compute='_compute_conversion_rate',
        digits=(5, 2),
    )

    last_contact_date = fields.Date(
        string='Dernier contact',
        tracking=True,
    )

    days_since_last_contact = fields.Integer(
        string='Jours sans contact',
        compute='_compute_days_since_last_contact',
    )

    internal_notes = fields.Html(
        string='Notes internes CRM',
    )

    # --- Champs BTP ---
    btp_project_type = fields.Selection([
        ('renovation', 'Rénovation'),
        ('neuf', 'Construction neuve'),
        ('extension', 'Extension'),
        ('vrd', 'VRD (Voirie / Réseaux)'),
        ('second_oeuvre', 'Second œuvre'),
        ('autre', 'Autre'),
    ], string='Type de projet', tracking=True)

    btp_client_budget = fields.Float(
        string='Budget estimé client (DH)',
        digits=(15, 2),
        tracking=True,
    )

    btp_surface = fields.Float(
        string='Surface (m²)',
        digits=(10, 2),
    )

    btp_site_address = fields.Text(
        string='Adresse du chantier',
    )

    btp_site_city = fields.Char(
        string='Ville du chantier',
        tracking=True,
    )

    btp_start_date = fields.Date(
        string='Date de début souhaitée',
    )

    btp_visit_date = fields.Date(
        string='Date de visite sur site',
        tracking=True,
    )

    btp_visit_done = fields.Boolean(
        string='Visite effectuée',
        compute='_compute_btp_visit_done',
        store=True,
        readonly=False,
        tracking=True,
    )

    btp_loss_reason = fields.Selection([
        ('prix', 'Prix trop élevé'),
        ('delais', 'Délais trop longs'),
        ('concurrent', 'Concurrent moins cher'),
        ('technique', 'Problème technique'),
        ('annule', 'Client annulé'),
        ('autre', 'Autre'),
    ], string='Motif de perte', tracking=True)

    btp_is_lost_stage = fields.Boolean(
        string='Étape Perdu',
        compute='_compute_btp_is_lost_stage',
    )

    # --- Calculs ---
    @api.depends('expected_revenue', 'probability')
    def _compute_conversion_rate(self):
        for lead in self:
            lead.conversion_rate = (lead.expected_revenue or 0) * (lead.probability or 0) / 100

    @api.depends('btp_visit_date')
    def _compute_btp_visit_done(self):
        today = fields.Date.today()
        for lead in self:
            if lead.btp_visit_date:
                lead.btp_visit_done = lead.btp_visit_date <= today
            elif not lead.btp_visit_date:
                lead.btp_visit_done = False

    @api.depends('stage_id')
    def _compute_btp_is_lost_stage(self):
        for lead in self:
            lead.btp_is_lost_stage = bool(lead.stage_id and lead.stage_id.fold)

    @api.depends('probability')
    def _compute_lead_quality(self):
        for lead in self:
            if not lead.lead_quality:
                if lead.probability and lead.probability >= 50:
                    lead.lead_quality = 'hot'
                elif lead.probability and lead.probability >= 20:
                    lead.lead_quality = 'warm'
                else:
                    lead.lead_quality = 'cold'

    def _compute_meeting_count_custom(self):
        for lead in self:
            lead.meeting_count_custom = self.env['calendar.event'].search_count([
                ('opportunity_id', '=', lead.id)
            ]) if lead.id else 0

    def _compute_quote_count(self):
        for lead in self:
            lead.quote_count = self.env['sale.order'].search_count([
                ('opportunity_id', '=', lead.id)
            ]) if lead.id else 0

    def _compute_days_since_last_contact(self):
        today = fields.Date.today()
        for lead in self:
            if lead.last_contact_date:
                lead.days_since_last_contact = (today - lead.last_contact_date).days
            else:
                lead.days_since_last_contact = 0

    # --- Actions ---
    def action_log_call(self):
        """Enregistrer un appel"""
        for lead in self:
            lead.call_count += 1
            lead.last_contact_date = fields.Date.today()
            lead.message_post(
                body=_("Appel enregistré par %s (appel n°%d)") % (
                    self.env.user.name, lead.call_count
                ),
                subtype_xmlid='mail.mt_note',
            )

    def action_schedule_meeting(self):
        """Planifier un rendez-vous lié à l'opportunité"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Planifier un RDV'),
            'res_model': 'calendar.event',
            'view_mode': 'form',
            'context': {
                'default_opportunity_id': self.id,
                'default_partner_ids': [(4, self.partner_id.id)] if self.partner_id else [],
                'default_name': _('RDV - %s') % self.name,
            },
        }

    def action_quick_quotation(self):
        """Créer rapidement un devis depuis l'opportunité"""
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Veuillez d'abord définir un client pour cette opportunité."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nouveau devis'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_opportunity_id': self.id,
                'default_origin': self.name,
            },
        }

    def action_view_meetings(self):
        """Voir les rendez-vous liés"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rendez-vous'),
            'res_model': 'calendar.event',
            'view_mode': 'tree,form,calendar',
            'domain': [('opportunity_id', '=', self.id)],
        }

    def action_view_quotations(self):
        """Voir les devis liés"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Devis'),
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('opportunity_id', '=', self.id)],
        }

    def _get_primary_email(self):
        self.ensure_one()
        return self.email_from or self.partner_id.email

    def _get_primary_phone(self):
        self.ensure_one()
        return self.phone or self.mobile or self.partner_id.mobile or self.partner_id.phone

    def _format_whatsapp_phone(self, phone):
        if not phone:
            return ''
        clean = ''.join(c for c in phone if c.isdigit() or c == '+')
        if clean.startswith('0') and len(clean) == 10:
            clean = '+212' + clean[1:]
        elif clean.startswith('212') and not clean.startswith('+'):
            clean = '+' + clean
        return clean.lstrip('+')

    def action_open_gmail_compose(self):
        self.ensure_one()
        email = self._get_primary_email()
        if not email:
            raise UserError(_("Aucune adresse email n'est renseignée sur cette opportunité."))
        subject = quote(_("Suivi opportunité - %s") % self.name)
        body = quote(_("Bonjour,\n\nJe reviens vers vous au sujet de %s.\n\nCordialement,") % self.name)
        return {
            'type': 'ir.actions.act_url',
            'url': f"https://mail.google.com/mail/?view=cm&fs=1&to={quote(email)}&su={subject}&body={body}",
            'target': 'new',
        }

    def action_call_partner(self):
        self.ensure_one()
        phone = self._get_primary_phone()
        if not phone:
            raise UserError(_("Aucun numéro de téléphone n'est renseigné sur cette opportunité."))
        return {
            'type': 'ir.actions.act_url',
            'url': f"tel:{quote(phone)}",
            'target': 'self',
        }

    def action_open_whatsapp_chat(self):
        self.ensure_one()
        phone = False
        if self.partner_id and 'whatsapp_number' in self.partner_id._fields:
            phone = self.partner_id.whatsapp_number
        phone = self._format_whatsapp_phone(phone or self._get_primary_phone())
        if not phone:
            raise UserError(_("Aucun numéro WhatsApp exploitable n'est disponible sur cette opportunité."))
        message = quote(_("Bonjour, je vous contacte au sujet de %s.") % self.name)
        return {
            'type': 'ir.actions.act_url',
            'url': f"https://wa.me/{phone}?text={message}",
            'target': 'new',
        }

    # --- Actions BTP ---
    def action_schedule_site_visit(self):
        """Planifier une visite sur chantier"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Planifier visite chantier'),
            'res_model': 'calendar.event',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_opportunity_id': self.id,
                'default_partner_ids': [(4, self.partner_id.id)] if self.partner_id else [],
                'default_name': _('Visite chantier – %s') % self.name,
                'default_description': self.btp_site_address or '',
            },
        }

    def action_mark_visit_done(self):
        """Marquer la visite sur site comme effectuée (et avancer l'étape si besoin)"""
        for lead in self:
            vals = {'btp_visit_done': True}
            if not lead.btp_visit_date:
                vals['btp_visit_date'] = fields.Date.today()
            # Avancer automatiquement vers « Visite effectuée » si on est à « Visite programmée »
            if lead.stage_id and lead.stage_id.sequence == 30:
                next_stage = self.env['crm.stage'].search(
                    [('sequence', '=', 40)], limit=1
                )
                if next_stage:
                    vals['stage_id'] = next_stage.id
            lead.write(vals)
        return True

    def action_open_btp_lost_wizard(self):
        """Ouvrir le dialogue de perte BTP"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Marquer comme perdu'),
            'res_model': 'crm.lead.btp.lost.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_btp_loss_reason': self.btp_loss_reason or 'autre',
            },
        }


class CrmCompetitor(models.Model):
    _name = 'crm.competitor'
    _description = 'Concurrent'

    name = fields.Char(string='Nom', required=True)
    website = fields.Char(string='Site web')
    notes = fields.Text(string='Notes')
    strength = fields.Text(string='Points forts')
    weakness = fields.Text(string='Points faibles')
    active = fields.Boolean(default=True)


class CrmLeadBtpLostWizard(models.TransientModel):
    _name = 'crm.lead.btp.lost.wizard'
    _description = 'Assistant – Motif de perte BTP'

    lead_id = fields.Many2one('crm.lead', string='Opportunité', required=True, ondelete='cascade')
    btp_loss_reason = fields.Selection([
        ('prix', 'Prix trop élevé'),
        ('delais', 'Délais trop longs'),
        ('concurrent', 'Concurrent moins cher'),
        ('technique', 'Problème technique'),
        ('annule', 'Client annulé'),
        ('autre', 'Autre'),
    ], string='Motif de perte', required=True, default='autre')

    def action_confirm_lost(self):
        """Confirmer la perte : déplacer l'opportunité vers l'étape Perdu."""
        self.ensure_one()
        perdu_stage = self.env['crm.stage'].search([('name', '=', 'Perdu')], limit=1)
        vals = {
            'btp_loss_reason': self.btp_loss_reason,
            'probability': 0,
        }
        if perdu_stage:
            vals['stage_id'] = perdu_stage.id
        self.lead_id.write(vals)
        return {'type': 'ir.actions.act_window_close'}
