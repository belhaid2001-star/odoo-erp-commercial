# -*- coding: utf-8 -*-
"""
Modèle btp.engin — Engins de chantier, hérite de maintenance.equipment
"""

from odoo import models, fields, api
from datetime import date, timedelta


class BtpEngin(models.Model):
    _name = 'btp.engin'
    _description = 'Engin BTP'
    _inherit = ['mail.thread']
    _order = 'name'

    # ──────────────── Identification ────────────────
    name = fields.Char(string='Nom / Désignation', required=True)
    immatriculation = fields.Char(string='Immatriculation')
    image = fields.Binary(string='Photo')

    # ──────────────── Type ────────────────
    type_engin = fields.Selection([
        ('pelle', 'Pelle hydraulique'),
        ('chargeuse', 'Chargeuse'),
        ('grue', 'Grue'),
        ('camion', 'Camion'),
        ('compacteur', 'Compacteur'),
        ('betonniere', 'Bétonnière'),
        ('groupe_electrogene', 'Groupe électrogène'),
        ('pompe', 'Pompe'),
    ], string='Type d\'engin', required=True)

    # ──────────────── Consommation ────────────────
    compteur_heures = fields.Float(string='Compteur heures')
    consommation_gasoil_heure = fields.Float(string='Consommation gasoil/heure (L)')
    cout_heure = fields.Float(string='Coût horaire (DH)')

    # ──────────────── Affectation ────────────────
    chantier_id = fields.Many2one('btp.chantier', string='Chantier affecté')

    # ──────────────── État ────────────────
    state = fields.Selection([
        ('disponible', 'Disponible'),
        ('en_service', 'En service'),
        ('en_panne', 'En panne'),
        ('en_maintenance', 'En maintenance'),
    ], string='État', default='disponible', tracking=True, group_expand='_expand_states')

    # ──────────────── Documents ────────────────
    assurance_date_fin = fields.Date(string='Fin assurance')
    visite_technique_date_fin = fields.Date(string='Fin visite technique')

    # ──────────────── Alertes ────────────────
    alerte_assurance = fields.Boolean(compute='_compute_alertes', store=True)
    alerte_visite = fields.Boolean(compute='_compute_alertes', store=True)

    # ──────────────── Relations ────────────────
    pointage_ids = fields.One2many('btp.engin.pointage', 'engin_id', string='Pointages engin')
    # ──────────────── Couleur Kanban ────────────────
    color = fields.Integer(string='Couleur')

    # ──────────────── Calculs ────────────────
    @api.depends('assurance_date_fin', 'visite_technique_date_fin')
    def _compute_alertes(self):
        today = date.today()
        for rec in self:
            rec.alerte_assurance = bool(rec.assurance_date_fin and rec.assurance_date_fin <= today + timedelta(days=30))
            rec.alerte_visite = bool(rec.visite_technique_date_fin and rec.visite_technique_date_fin <= today + timedelta(days=30))

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    # ──────────────── Actions ────────────────
    def action_mettre_en_service(self):
        self.write({'state': 'en_service'})

    def action_declarer_panne(self):
        self.write({'state': 'en_panne'})

    def action_rendre_disponible(self):
        self.write({'state': 'disponible'})

    _sql_constraints = [
        ('immat_unique', 'unique(immatriculation)', 'L\'immatriculation doit être unique !'),
    ]
