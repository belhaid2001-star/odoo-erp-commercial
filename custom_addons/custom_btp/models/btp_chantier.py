# -*- coding: utf-8 -*-
"""
Modèle principal : btp.chantier
Hérite de project.project pour la gestion complète des chantiers BTP au Maroc.
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class BtpChantier(models.Model):
    _name = 'btp.chantier'
    _description = 'Chantier BTP'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ──────────────── Informations générales ────────────────
    name = fields.Char(string='Nom du chantier', required=True, tracking=True)
    reference = fields.Char(string='Référence', readonly=True, copy=False, default='Nouveau')
    project_id = fields.Many2one('project.project', string='Projet Odoo', ondelete='set null')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    description = fields.Html(string='Description')

    # ──────────────── Localisation ────────────────
    adresse_chantier = fields.Text(string='Adresse du chantier')
    ville = fields.Char(string='Ville')
    coordonnees_gps = fields.Char(string='Coordonnées GPS')

    # ──────────────── Intervenants ────────────────
    maitre_ouvrage_id = fields.Many2one('res.partner', string='Maître d\'ouvrage', tracking=True)
    maitre_oeuvre_id = fields.Many2one('res.partner', string='Maître d\'œuvre', tracking=True)
    architecte_id = fields.Many2one('res.partner', string='Architecte')
    bureau_controle_id = fields.Many2one('res.partner', string='Bureau de contrôle')
    responsable_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user, tracking=True)

    # ──────────────── Dates ────────────────
    date_debut_prev = fields.Date(string='Date début prévue')
    date_debut_reel = fields.Date(string='Date début réelle')
    date_fin_prev = fields.Date(string='Date fin prévue')
    date_fin_reel = fields.Date(string='Date fin réelle')
    duree_prev_jours = fields.Integer(string='Durée prévue (jours)', compute='_compute_durees', store=True)
    retard_jours = fields.Integer(string='Retard (jours)', compute='_compute_durees', store=True)

    # ──────────────── Montants ────────────────
    montant_contrat = fields.Monetary(string='Montant du contrat', currency_field='currency_id', tracking=True)
    montant_avenant = fields.Monetary(string='Montant des avenants', currency_field='currency_id')
    montant_total = fields.Monetary(string='Montant total', compute='_compute_montant_total', store=True, currency_field='currency_id')

    # ──────────────── Retenue de garantie ────────────────
    taux_retenue_garantie = fields.Selection([
        ('5', '5%'),
        ('10', '10%'),
    ], string='Taux retenue de garantie', default='5')
    montant_retenue = fields.Monetary(string='Montant retenue', compute='_compute_montant_retenue', store=True, currency_field='currency_id')

    # ──────────────── Type de marché ────────────────
    type_marche = fields.Selection([
        ('prive', 'Marché privé'),
        ('public', 'Marché public'),
        ('bon_commande', 'Bon de commande'),
    ], string='Type de marché', default='prive', required=True, tracking=True)
    numero_marche = fields.Char(string='Numéro de marché')

    # ──────────────── Cautions ────────────────
    caution_provisoire = fields.Monetary(string='Caution provisoire', currency_field='currency_id')
    caution_definitive = fields.Monetary(string='Caution définitive', currency_field='currency_id')

    # ──────────────── État ────────────────
    state = fields.Selection([
        ('etude', 'Étude'),
        ('appel_offres', 'Appel d\'offres'),
        ('attribue', 'Attribué'),
        ('ordre_service', 'Ordre de service'),
        ('en_cours', 'En cours'),
        ('arret', 'Arrêt'),
        ('reprise', 'Reprise'),
        ('reception_prov', 'Réception provisoire'),
        ('levee_reserves', 'Levée des réserves'),
        ('reception_def', 'Réception définitive'),
        ('cloture', 'Clôturé'),
    ], string='État', default='etude', required=True, tracking=True, group_expand='_expand_states')

    # ──────────────── Avancement ────────────────
    taux_avancement = fields.Float(string='Taux d\'avancement (%)', compute='_compute_taux_avancement', store=True)

    # ──────────────── Pénalités ────────────────
    penalite_retard = fields.Monetary(string='Pénalité de retard', compute='_compute_penalite', store=True, currency_field='currency_id')

    # ──────────────── Révision des prix (marchés publics) ────────────────
    indice_bt_base = fields.Float(string='Indice BT de base', digits=(12, 4))
    indice_bt_actuel = fields.Float(string='Indice BT actuel', digits=(12, 4))

    # ──────────────── Relations ────────────────
    lot_ids = fields.One2many('btp.lot', 'chantier_id', string='Lots')
    tache_ids = fields.One2many('btp.tache', 'chantier_id', string='Tâches')
    situation_ids = fields.One2many('btp.situation', 'chantier_id', string='Situations')
    document_ids = fields.One2many('btp.document', 'chantier_id', string='Documents')
    reception_ids = fields.One2many('btp.reception', 'chantier_id', string='Réceptions')
    reunion_ids = fields.One2many('btp.reunion', 'chantier_id', string='Réunions')
    sous_traitant_ids = fields.Many2many('btp.sous.traitant', string='Sous-traitants')
    ressource_ids = fields.Many2many('btp.ressource', string='Ressources')
    engin_ids = fields.One2many('btp.engin', 'chantier_id', string='Engins')
    pointage_ids = fields.One2many('btp.pointage', 'chantier_id', string='Pointages')
    meteo_ids = fields.One2many('btp.meteo', 'chantier_id', string='Météo')
    approvisionnement_ids = fields.One2many('btp.approvisionnement', 'chantier_id', string='Approvisionnements')

    # ──────────────── GED : pièces jointes du chantier ────────────────
    ged_document_count = fields.Integer(compute='_compute_ged_document_count', string='Documents GED')

    # ──────────────── Consommation globale lots ────────────────
    taux_consommation_global = fields.Float(
        string='Consommation globale (%)',
        compute='_compute_taux_consommation_global',
        store=True,
        help="Taux de consommation budgétaire moyen pondéré de tous les lots du chantier.",
    )

    # ──────────────── Compteurs ────────────────
    lot_count = fields.Integer(compute='_compute_counts')
    situation_count = fields.Integer(compute='_compute_counts')
    document_count = fields.Integer(compute='_compute_counts')
    reception_count = fields.Integer(compute='_compute_counts')
    reunion_count = fields.Integer(compute='_compute_counts')
    engin_count = fields.Integer(compute='_compute_counts')

    # ──────────────── Couleur Kanban ────────────────
    color = fields.Integer(string='Couleur')
    kanban_state = fields.Selection([
        ('normal', 'Normal'),
        ('done', 'Terminé'),
        ('blocked', 'Bloqué'),
    ], default='normal')

    # ──────────────── SQL Constraints ────────────────
    _sql_constraints = [
        ('reference_unique', 'unique(reference)', 'La référence du chantier doit être unique !'),
        ('montant_contrat_positive', 'CHECK(montant_contrat >= 0)', 'Le montant du contrat doit être positif !'),
    ]

    # ──────────────── Méthodes de calcul ────────────────
    @api.depends('date_debut_prev', 'date_fin_prev', 'date_fin_reel')
    def _compute_durees(self):
        for rec in self:
            # Durée prévue
            if rec.date_debut_prev and rec.date_fin_prev:
                rec.duree_prev_jours = (rec.date_fin_prev - rec.date_debut_prev).days
            else:
                rec.duree_prev_jours = 0
            # Retard
            if rec.date_fin_prev and rec.state not in ('cloture', 'reception_def'):
                date_ref = rec.date_fin_reel or fields.Date.today()
                retard = (date_ref - rec.date_fin_prev).days
                rec.retard_jours = max(0, retard)
            else:
                rec.retard_jours = 0

    @api.depends('montant_contrat', 'montant_avenant')
    def _compute_montant_total(self):
        for rec in self:
            rec.montant_total = rec.montant_contrat + (rec.montant_avenant or 0.0)

    @api.depends('montant_total', 'taux_retenue_garantie')
    def _compute_montant_retenue(self):
        for rec in self:
            taux = float(rec.taux_retenue_garantie or '5') / 100.0
            rec.montant_retenue = rec.montant_total * taux

    @api.depends('situation_ids', 'situation_ids.taux_avancement', 'situation_ids.state')
    def _compute_taux_avancement(self):
        for rec in self:
            situations = rec.situation_ids.filtered(lambda s: s.state in ('valide', 'facture', 'paye'))
            if situations:
                rec.taux_avancement = max(situations.mapped('taux_avancement'))
            else:
                rec.taux_avancement = 0.0

    @api.depends('montant_total', 'retard_jours')
    def _compute_penalite(self):
        """Pénalité de retard : 1‰ par jour, plafonnée à 10% du montant du marché"""
        for rec in self:
            if rec.retard_jours > 0 and rec.montant_total > 0:
                penalite = rec.montant_total * 0.001 * rec.retard_jours
                plafond = rec.montant_total * 0.10
                rec.penalite_retard = min(penalite, plafond)
            else:
                rec.penalite_retard = 0.0

    def _compute_counts(self):
        for rec in self:
            rec.lot_count = len(rec.lot_ids)
            rec.situation_count = len(rec.situation_ids)
            rec.document_count = len(rec.document_ids)
            rec.reception_count = len(rec.reception_ids)
            rec.reunion_count = len(rec.reunion_ids)
            rec.engin_count = len(rec.engin_ids)

    def _compute_ged_document_count(self):
        AttModel = self.env['ir.attachment']
        for rec in self:
            rec.ged_document_count = AttModel.search_count([
                ('res_model', '=', 'btp.chantier'),
                ('res_id', '=', rec.id),
            ])

    @api.depends('lot_ids', 'lot_ids.budget_prevu', 'lot_ids.cout_reel')
    def _compute_taux_consommation_global(self):
        """Taux de consommation budgétaire global : coût réel total / budget total des lots."""
        for rec in self:
            budget_total = sum(rec.lot_ids.mapped('budget_prevu'))
            cout_total = sum(rec.lot_ids.mapped('cout_reel'))
            if budget_total:
                rec.taux_consommation_global = (cout_total / budget_total) * 100
            else:
                rec.taux_consommation_global = 0.0

    def _expand_states(self, states, domain, order):
        """Afficher tous les états dans la vue Kanban"""
        return [key for key, val in type(self).state.selection]

    # ──────────────── Séquence ────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('btp.chantier') or 'Nouveau'
        return super().create(vals_list)

    def _ensure_project(self):
        """Garantit un projet Odoo pour synchroniser les tâches chantier avec le To-Do global."""
        Project = self.env['project.project']
        for rec in self:
            if rec.project_id:
                continue
            project_vals = {
                'name': rec.reference and f"[{rec.reference}] {rec.name}" or rec.name,
            }
            if 'partner_id' in Project._fields and rec.maitre_ouvrage_id:
                project_vals['partner_id'] = rec.maitre_ouvrage_id.id
            rec.project_id = Project.create(project_vals)
        return self.project_id

    # ──────────────── Actions de workflow ────────────────
    def action_appel_offres(self):
        self.write({'state': 'appel_offres'})

    def action_attribuer(self):
        self.write({'state': 'attribue'})

    def action_ordre_service(self):
        self.write({'state': 'ordre_service'})

    def action_demarrer(self):
        vals = {'state': 'en_cours'}
        if not self.date_debut_reel:
            vals['date_debut_reel'] = fields.Date.today()
        self.write(vals)

    def action_arreter(self):
        self.write({'state': 'arret'})

    def action_reprendre(self):
        self.write({'state': 'reprise'})

    def action_reception_provisoire(self):
        self.write({'state': 'reception_prov'})

    def action_levee_reserves(self):
        self.write({'state': 'levee_reserves'})

    def action_reception_definitive(self):
        self.write({'state': 'reception_def'})

    def action_cloturer(self):
        self.write({'state': 'cloture', 'date_fin_reel': fields.Date.today()})

    # ──────────────── Calcul révision des prix (marchés publics) ────────────────
    def calculer_revision_prix(self):
        """Formule : P = P0 × (0.15 + 0.85 × BT_actuel / BT_base)"""
        self.ensure_one()
        if self.type_marche != 'public':
            raise ValidationError("La révision des prix ne s'applique qu'aux marchés publics.")
        if not self.indice_bt_base or not self.indice_bt_actuel:
            raise ValidationError("Veuillez renseigner les indices BT de base et actuel.")
        coefficient = 0.15 + 0.85 * (self.indice_bt_actuel / self.indice_bt_base)
        montant_revise = self.montant_contrat * coefficient
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Révision des prix',
                'message': f'Coefficient de révision : {coefficient:.4f}\nMontant révisé : {montant_revise:,.2f} DH',
                'type': 'info',
                'sticky': True,
            }
        }

    # ──────────────── Smart Buttons ────────────────
    def action_view_lots(self):
        return {
            'name': 'Lots',
            'type': 'ir.actions.act_window',
            'res_model': 'btp.lot',
            'view_mode': 'tree,form',
            'domain': [('chantier_id', '=', self.id)],
            'context': {'default_chantier_id': self.id},
        }

    def action_view_situations(self):
        return {
            'name': 'Situations',
            'type': 'ir.actions.act_window',
            'res_model': 'btp.situation',
            'view_mode': 'tree,form',
            'domain': [('chantier_id', '=', self.id)],
            'context': {'default_chantier_id': self.id},
        }

    def action_view_documents(self):
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'btp.document',
            'view_mode': 'tree,form',
            'domain': [('chantier_id', '=', self.id)],
            'context': {'default_chantier_id': self.id},
        }

    def action_view_receptions(self):
        return {
            'name': 'Réceptions',
            'type': 'ir.actions.act_window',
            'res_model': 'btp.reception',
            'view_mode': 'tree,form',
            'domain': [('chantier_id', '=', self.id)],
            'context': {'default_chantier_id': self.id},
        }

    def action_view_reunions(self):
        return {
            'name': 'Réunions',
            'type': 'ir.actions.act_window',
            'res_model': 'btp.reunion',
            'view_mode': 'tree,form',
            'domain': [('chantier_id', '=', self.id)],
            'context': {'default_chantier_id': self.id},
        }

    def action_view_engins(self):
        return {
            'name': 'Engins',
            'type': 'ir.actions.act_window',
            'res_model': 'btp.engin',
            'view_mode': 'tree,kanban,form',
            'domain': [('chantier_id', '=', self.id)],
            'context': {'default_chantier_id': self.id},
        }

    def action_view_ged_documents(self):
        """Ouvrir les pièces jointes du chantier."""
        self.ensure_one()
        return {
            'name': 'Documents — ' + self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [('res_model', '=', 'btp.chantier'), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': 'btp.chantier',
                'default_res_id': self.id,
            },
        }

    # ──────────────── Cron journalier : alertes ────────────────
    @api.model
    def _cron_check_alertes(self):
        """
        Vérifie quotidiennement :
        - Documents expirés ou proches de l'expiration
        - Engins en panne
        - Chantiers en retard
        - Décisions de réunion en retard
        """
        today = fields.Date.today()

        # 1. Documents expirés
        documents = self.env['btp.document'].search([
            ('date_expiration', '<=', today),
            ('date_expiration', '!=', False),
        ])
        for doc in documents:
            doc.chantier_id.message_post(
                body=f"⚠️ Document expiré : {doc.name} (type: {doc.type_document})",
                subject="Alerte : Document expiré",
            )

        # 2. Engins en panne
        engins = self.env['btp.engin'].search([('state', '=', 'en_panne')])
        for engin in engins:
            if engin.chantier_id:
                engin.chantier_id.message_post(
                    body=f"🔧 Engin en panne : {engin.name} ({engin.immatriculation or ''})",
                    subject="Alerte : Engin en panne",
                )

        # 3. Chantiers en retard
        chantiers = self.search([
            ('state', 'in', ('en_cours', 'reprise')),
            ('date_fin_prev', '<', today),
        ])
        for chantier in chantiers:
            chantier.message_post(
                body=f"⏰ Chantier en retard de {chantier.retard_jours} jour(s). Pénalité estimée : {chantier.penalite_retard:,.2f} DH",
                subject="Alerte : Retard chantier",
            )

        # 4. Décisions en retard
        decisions = self.env['btp.decision'].search([
            ('state', '=', 'en_cours'),
            ('date_echeance', '<', today),
        ])
        decisions.write({'state': 'retard'})
