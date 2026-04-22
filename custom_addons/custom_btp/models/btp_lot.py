# -*- coding: utf-8 -*-
"""
Modèle btp.lot — Lots de chantier BTP
"""

from odoo import models, fields, api


class BtpLot(models.Model):
    _name = 'btp.lot'
    _description = 'Lot de chantier BTP'
    _order = 'sequence, id'
    _inherit = ['mail.thread']

    # ──────────────── Champs principaux ────────────────
    name = fields.Char(string='Nom du lot', required=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Séquence', default=10)
    chantier_id = fields.Many2one('btp.chantier', string='Chantier', required=True, ondelete='cascade')
    responsable_id = fields.Many2one('res.users', string='Responsable')
    company_id = fields.Many2one(related='chantier_id.company_id', store=True)
    currency_id = fields.Many2one(related='chantier_id.currency_id', store=True)

    # ──────────────── Budget ────────────────
    budget_prevu = fields.Monetary(string='Budget prévu', currency_field='currency_id')
    cout_reel = fields.Monetary(string='Coût réel', compute='_compute_couts', store=True, currency_field='currency_id')
    ecart = fields.Monetary(string='Écart', compute='_compute_couts', store=True, currency_field='currency_id')
    taux_consommation = fields.Float(string='Taux de consommation (%)', compute='_compute_couts', store=True)

    # ──────────────── Relations ────────────────
    tache_ids = fields.One2many('btp.tache', 'lot_id', string='Tâches')
    meteo_ids = fields.One2many('btp.meteo', 'lot_id', string='Suivi météo')
    situation_line_ids = fields.One2many('btp.situation.line', 'lot_id', string='Lignes de situation')

    # ──────────────── Calculs ────────────────
    @api.depends('situation_line_ids', 'situation_line_ids.montant_cumule', 'budget_prevu')
    def _compute_couts(self):
        for rec in self:
            # Coût réel = somme des montants cumulés des lignes de situation validées
            lines = rec.situation_line_ids.filtered(
                lambda l: l.situation_id.state in ('valide', 'facture', 'paye'))
            if lines:
                rec.cout_reel = sum(lines.mapped('montant_cumule'))
            else:
                rec.cout_reel = 0.0
            rec.ecart = rec.budget_prevu - rec.cout_reel
            if rec.budget_prevu:
                rec.taux_consommation = (rec.cout_reel / rec.budget_prevu) * 100
            else:
                rec.taux_consommation = 0.0

    _sql_constraints = [
        ('budget_positive', 'CHECK(budget_prevu >= 0)', 'Le budget prévu doit être positif !'),
    ]
