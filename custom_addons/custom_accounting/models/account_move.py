# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    # --- Champs personnalisés ---
    payment_reminder_sent = fields.Boolean(
        string='Relance envoyée',
        default=False,
        tracking=True,
    )

    last_reminder_date = fields.Date(
        string='Dernière relance',
        readonly=True,
    )

    reminder_count = fields.Integer(
        string='Nombre de relances',
        default=0,
    )

    days_overdue = fields.Integer(
        string='Jours de retard',
        compute='_compute_days_overdue',
        store=True,
    )

    risk_level = fields.Selection([
        ('low', 'Faible'),
        ('medium', 'Moyen'),
        ('high', 'Élevé'),
        ('critical', 'Critique'),
    ], string='Niveau de risque',
        compute='_compute_risk_level',
        store=True,
    )

    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag.custom',
        string='Étiquettes analytiques',
    )

    validated_by = fields.Many2one(
        'res.users',
        string='Validé par',
        readonly=True,
    )

    validation_date = fields.Datetime(
        string='Date de validation',
        readonly=True,
    )

    internal_notes = fields.Text(
        string='Notes internes',
    )

    cheque_ids = fields.One2many(
        'account.cheque',
        'move_id',
        string='Chèques',
    )

    # ──────────────── Liaison Stock & Inventaire ────────────────
    picking_ids = fields.Many2many(
        'stock.picking',
        'account_move_stock_picking_rel',
        'move_id',
        'picking_id',
        string='Bons de livraison / Réceptions',
        help="Opérations de stock liées à cette pièce comptable.",
    )
    picking_count = fields.Integer(
        string='Nb mouvements stock',
        compute='_compute_picking_count',
    )

    # ──────────────── Documents justificatifs ────────────────
    doc_attachment_ids = fields.Many2many(
        'ir.attachment',
        'account_move_doc_attachment_rel',
        'move_id',
        'attachment_id',
        string='Pièces justificatives',
        help="Documents justificatifs liés à cette écriture comptable : bons de commande, contrats, bons de livraison, etc.",
    )

    def _compute_picking_count(self):
        for move in self:
            move.picking_count = len(move.picking_ids)

    def action_view_pickings(self):
        """Ouvrir les mouvements de stock liés."""
        self.ensure_one()
        return {
            'name': 'Mouvements de stock',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.picking_ids.ids)],
        }

    # --- Calculs ---
    @api.depends('invoice_date_due', 'payment_state')
    def _compute_days_overdue(self):
        today = fields.Date.today()
        for move in self:
            if move.invoice_date_due and move.payment_state not in ('paid', 'reversed'):
                delta = (today - move.invoice_date_due).days
                move.days_overdue = max(0, delta)
            else:
                move.days_overdue = 0

    @api.depends('days_overdue', 'amount_residual')
    def _compute_risk_level(self):
        for move in self:
            if move.days_overdue > 90 or move.amount_residual > 100000:
                move.risk_level = 'critical'
            elif move.days_overdue > 60 or move.amount_residual > 50000:
                move.risk_level = 'high'
            elif move.days_overdue > 30:
                move.risk_level = 'medium'
            else:
                move.risk_level = 'low'

    # --- Actions ---
    def action_send_payment_reminder(self):
        """Envoyer une relance de paiement"""
        for move in self:
            if move.payment_state == 'paid':
                raise UserError(_("Cette facture est déjà payée."))
            
            # Envoyer un message de relance
            move.message_post(
                body=_(
                    "Relance de paiement n°%d envoyée pour la facture %s. "
                    "Montant restant dû : %s %s. Échéance : %s."
                ) % (
                    move.reminder_count + 1,
                    move.name,
                    move.amount_residual,
                    move.currency_id.symbol,
                    move.invoice_date_due,
                ),
                subtype_xmlid='mail.mt_comment',
                partner_ids=move.partner_id.ids,
            )
            
            move.write({
                'payment_reminder_sent': True,
                'last_reminder_date': fields.Date.today(),
                'reminder_count': move.reminder_count + 1,
            })

    def action_validate_invoice(self):
        """Validation personnalisée avec traçabilité"""
        for move in self:
            move.write({
                'validated_by': self.env.user.id,
                'validation_date': fields.Datetime.now(),
            })
            move.message_post(
                body=_("Facture validée par %s") % self.env.user.name,
                subtype_xmlid='mail.mt_note',
            )

    @api.model
    def _cron_send_overdue_reminders(self):
        """Cron pour envoyer automatiquement les relances"""
        overdue_invoices = self.search([
            ('move_type', 'in', ['out_invoice']),
            ('payment_state', 'not in', ['paid', 'reversed']),
            ('invoice_date_due', '<', fields.Date.today()),
            ('state', '=', 'posted'),
        ])
        for invoice in overdue_invoices:
            # Relance hebdomadaire
            if not invoice.last_reminder_date or \
               (fields.Date.today() - invoice.last_reminder_date).days >= 7:
                invoice.action_send_payment_reminder()


class AccountAnalyticTagCustom(models.Model):
    _name = 'account.analytic.tag.custom'
    _description = 'Étiquette analytique personnalisée'

    name = fields.Char(string='Nom', required=True)
    color = fields.Integer(string='Couleur')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company,
    )
