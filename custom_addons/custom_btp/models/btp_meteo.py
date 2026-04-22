# -*- coding: utf-8 -*-
"""
Modèle btp.meteo — Suivi météo chantier (justification retards)
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BtpMeteo(models.Model):
    _name = 'btp.meteo'
    _description = 'Météo Chantier BTP'
    _order = 'date desc'

    # ──────────────── Références ────────────────
    chantier_id = fields.Many2one('btp.chantier', string='Chantier', required=True, ondelete='cascade')
    lot_id = fields.Many2one('btp.lot', string='Lot', ondelete='cascade')
    tache_id = fields.Many2one('btp.tache', string='Tâche', ondelete='cascade')

    # ──────────────── Données ────────────────
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    intemperie = fields.Boolean(string='Intempérie', default=False)
    description = fields.Text(string='Description')

    # ──────────────── Impact ────────────────
    impact_travaux = fields.Selection([
        ('aucun', 'Aucun impact'),
        ('ralenti', 'Travaux ralentis'),
        ('arret', 'Arrêt des travaux'),
    ], string='Impact sur les travaux', default='aucun')

    # ──────────────── Justificatif ────────────────
    justificatif = fields.Binary(string='Justificatif')
    justificatif_filename = fields.Char(string='Nom fichier')

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id:
            self.chantier_id = self.lot_id.chantier_id

    @api.onchange('tache_id')
    def _onchange_tache_id(self):
        if self.tache_id:
            self.lot_id = self.tache_id.lot_id
            self.chantier_id = self.tache_id.chantier_id

    @api.constrains('chantier_id', 'lot_id', 'tache_id')
    def _check_links(self):
        for rec in self:
            if rec.lot_id and rec.lot_id.chantier_id != rec.chantier_id:
                raise ValidationError("Le lot sélectionné doit appartenir au chantier indiqué.")
            if rec.tache_id and rec.tache_id.chantier_id != rec.chantier_id:
                raise ValidationError("La tâche sélectionnée doit appartenir au chantier indiqué.")
            if rec.tache_id and rec.lot_id and rec.tache_id.lot_id != rec.lot_id:
                raise ValidationError("La tâche sélectionnée doit appartenir au lot indiqué.")
