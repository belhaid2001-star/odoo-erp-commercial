# -*- coding: utf-8 -*-
"""
Extensions des modèles tiers pour ajouter les relations
Document GED (One2many + smart buttons) sans modifier les modules source.
"""
from odoo import models, fields, api, _


class SaleOrderDocuments(models.Model):
    _inherit = 'sale.order'

    ged_document_ids = fields.One2many(
        'document.document', 'sale_id',
        string='Documents GED',
    )
    ged_document_count = fields.Integer(
        string='Documents GED',
        compute='_compute_ged_sale_count',
    )

    def _compute_ged_sale_count(self):
        for rec in self:
            rec.ged_document_count = self.env['document.document'].search_count(
                [('sale_id', '=', rec.id)]
            )

    def action_view_ged_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents — %s') % self.name,
            'res_model': 'document.document',
            'view_mode': 'list,kanban,form',
            'domain': [('sale_id', '=', self.id)],
            'context': {
                'default_sale_id': self.id,
                'default_name': self.name,
            },
        }


class PurchaseOrderDocuments(models.Model):
    _inherit = 'purchase.order'

    ged_document_ids = fields.One2many(
        'document.document', 'purchase_id',
        string='Documents GED',
    )
    ged_document_count = fields.Integer(
        string='Documents GED',
        compute='_compute_ged_purchase_count',
    )

    def _compute_ged_purchase_count(self):
        for rec in self:
            rec.ged_document_count = self.env['document.document'].search_count(
                [('purchase_id', '=', rec.id)]
            )

    def action_view_ged_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents — %s') % self.name,
            'res_model': 'document.document',
            'view_mode': 'list,kanban,form',
            'domain': [('purchase_id', '=', self.id)],
            'context': {
                'default_purchase_id': self.id,
                'default_name': self.name,
            },
        }


class AccountMoveDocuments(models.Model):
    _inherit = 'account.move'

    ged_document_ids = fields.One2many(
        'document.document', 'invoice_id',
        string='Documents GED',
    )
    # Champ Many2many séparé pour lier des documents GED existants
    ged_linked_docs = fields.Many2many(
        'document.document',
        'account_move_linked_doc_rel',
        'move_id',
        'doc_id',
        string='Documents liés (GED)',
        help='Sélectionnez des documents existants de la GED à associer à cette écriture.',
    )
    ged_document_count = fields.Integer(
        string='Documents GED',
        compute='_compute_ged_invoice_count',
    )

    def _compute_ged_invoice_count(self):
        for rec in self:
            rec.ged_document_count = len(rec.ged_document_ids) + len(rec.ged_linked_docs)

    def action_view_ged_documents(self):
        self.ensure_one()
        all_ids = self.ged_document_ids.ids + self.ged_linked_docs.ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents — %s') % self.name,
            'res_model': 'document.document',
            'view_mode': 'list,kanban,form',
            'domain': [('id', 'in', all_ids)],
            'context': {
                'default_invoice_id': self.id,
                'default_name': self.name,
            },
        }


class HrEmployeeDocuments(models.Model):
    _inherit = 'hr.employee'

    ged_document_ids = fields.One2many(
        'document.document', 'employee_id',
        string='Documents GED',
    )
    ged_document_count = fields.Integer(
        string='Documents GED',
        compute='_compute_ged_employee_count',
    )

    def _compute_ged_employee_count(self):
        for rec in self:
            rec.ged_document_count = self.env['document.document'].search_count(
                [('employee_id', '=', rec.id)]
            )

    def action_view_ged_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents — %s') % self.name,
            'res_model': 'document.document',
            'view_mode': 'list,kanban,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
                'default_name': self.name,
            },
        }
