# -*- coding: utf-8 -*-
"""
Modèle btp.tache — Tâches de chantier BTP avec support hiérarchique
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BtpTache(models.Model):
    _name = 'btp.tache'
    _description = 'Tâche BTP'
    _order = 'date_debut, sequence, id'
    _inherit = ['mail.thread']

    # ──────────────── Champs principaux ────────────────
    name = fields.Char(string='Nom de la tâche', required=True)
    sequence = fields.Integer(default=10)
    lot_id = fields.Many2one('btp.lot', string='Lot', required=True, ondelete='cascade')
    chantier_id = fields.Many2one('btp.chantier', string='Chantier', related='lot_id.chantier_id', store=True)
    project_task_id = fields.Many2one('project.task', string='Tâche To-Do', readonly=True, copy=False, ondelete='set null')

    # ──────────────── Hiérarchie ────────────────
    parent_id = fields.Many2one('btp.tache', string='Tâche parente', ondelete='cascade')
    child_ids = fields.One2many('btp.tache', 'parent_id', string='Sous-tâches')

    # ──────────────── Planification ────────────────
    date_debut = fields.Date(string='Date début')
    date_fin = fields.Date(string='Date fin')
    duree_prevue = fields.Float(string='Durée prévue (jours)')
    duree_reelle = fields.Float(string='Durée réelle (jours)', compute='_compute_duree_reelle', store=True)

    # ──────────────── Affectation ────────────────
    responsable_id = fields.Many2one('res.users', string='Responsable')
    dependance_ids = fields.Many2many('btp.tache', 'btp_tache_dependance_rel', 'tache_id', 'dependance_id', string='Dépendances')

    # ──────────────── État ────────────────
    state = fields.Selection([
        ('planifie', 'Planifié'),
        ('en_cours', 'En cours'),
        ('bloque', 'Bloqué'),
        ('termine', 'Terminé'),
    ], string='État', default='planifie', tracking=True, group_expand='_expand_states')

    priorite = fields.Selection([
        ('normale', 'Normale'),
        ('urgente', 'Urgente'),
        ('critique', 'Critique'),
    ], string='Priorité', default='normale')

    avancement = fields.Float(string='Avancement (%)', default=0.0)

    # ──────────────── Couleur Kanban ────────────────
    color = fields.Integer(string='Couleur')
    meteo_ids = fields.One2many('btp.meteo', 'tache_id', string='Suivi météo')

    # ──────────────── Calculs ────────────────
    @api.depends('chantier_id.pointage_ids', 'chantier_id.pointage_ids.heures_normales')
    def _compute_duree_reelle(self):
        for rec in self:
            pointages = self.env['btp.pointage'].search([('tache_id', '=', rec.id)])
            total_heures = sum(pointages.mapped('heures_normales'))
            rec.duree_reelle = total_heures / 8.0 if total_heures else 0.0

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    def _prepare_project_task_vals(self):
        self.ensure_one()
        project = self.chantier_id._ensure_project()
        description_parts = [
            f"Chantier : {self.chantier_id.name}",
            f"Lot : {self.lot_id.name}",
        ]
        if self.date_debut:
            description_parts.append(f"Début prévu : {self.date_debut}")
        if self.date_fin:
            description_parts.append(f"Fin prévue : {self.date_fin}")
        if self.priorite:
            description_parts.append(f"Priorité : {self.priorite}")
        return {
            'name': self.name,
            'project_id': project.id,
            'partner_id': self.chantier_id.maitre_ouvrage_id.id or False,
            'date_deadline': self.date_fin or False,
            'description': '\n'.join(description_parts),
            'user_ids': [(6, 0, [self.responsable_id.id])] if self.responsable_id else [(5, 0, 0)],
        }

    def _sync_project_task(self):
        Task = self.env['project.task'].with_context(mail_create_nosubscribe=True)
        for rec in self.filtered(lambda task: task.chantier_id):
            vals = rec._prepare_project_task_vals()
            if rec.project_task_id:
                rec.project_task_id.write(vals)
            else:
                task = Task.create(vals)
                rec.with_context(skip_btp_sync=True).write({'project_task_id': task.id})

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('skip_btp_sync'):
            records._sync_project_task()
        return records

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('skip_btp_sync'):
            return res
        sync_fields = {'name', 'lot_id', 'date_debut', 'date_fin', 'responsable_id', 'priorite'}
        if sync_fields.intersection(vals):
            self._sync_project_task()
        return res

    # ──────────────── Actions ────────────────
    def action_open_todo_task(self):
        self.ensure_one()
        if not self.project_task_id:
            self._sync_project_task()
        return {
            'name': 'To-Do global',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'res_id': self.project_task_id.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
        }

    def action_demarrer(self):
        self.write({'state': 'en_cours'})

    def action_bloquer(self):
        self.write({'state': 'bloque'})

    def action_terminer(self):
        self.write({'state': 'termine', 'avancement': 100.0})

    def action_replanifier(self):
        self.write({'state': 'planifie'})

    # ──────────────── Contraintes ────────────────
    @api.constrains('avancement')
    def _check_avancement(self):
        for rec in self:
            if rec.avancement < 0 or rec.avancement > 100:
                raise ValidationError("L'avancement doit être entre 0 et 100%.")

    @api.constrains('date_debut', 'date_fin')
    def _check_dates(self):
        for rec in self:
            if rec.date_debut and rec.date_fin and rec.date_fin < rec.date_debut:
                raise ValidationError("La date de fin doit être postérieure à la date de début.")
