# -*- coding: utf-8 -*-
"""
Modèle btp.approvisionnement — Approvisionnement chantier BTP
"""

from odoo import models, fields, api
from odoo.exceptions import UserError


class BtpApprovisionnement(models.Model):
    _name = 'btp.approvisionnement'
    _description = 'Approvisionnement BTP'
    _order = 'date_besoin desc'
    _inherit = ['mail.thread']

    # ──────────────── Références ────────────────
    chantier_id = fields.Many2one('btp.chantier', string='Chantier', required=True)
    lot_id = fields.Many2one('btp.lot', string='Lot')
    product_id = fields.Many2one('product.product', string='Article', required=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Bon de commande')

    # ──────────────── Quantités ────────────────
    quantite_demandee = fields.Float(string='Quantité demandée', required=True)
    quantite_livree = fields.Float(string='Quantité livrée', default=0.0)

    # ──────────────── Dates ────────────────
    date_besoin = fields.Date(string='Date du besoin', required=True)
    date_commande = fields.Date(string='Date commande')
    date_livraison_prevue = fields.Date(string='Date livraison prévue')
    date_livraison_reelle = fields.Date(string='Date livraison réelle')

    # ──────────────── État ────────────────
    state = fields.Selection([
        ('demande', 'Demande'),
        ('commande', 'Commandé'),
        ('partiel', 'Livraison partielle'),
        ('livre', 'Livré'),
    ], string='État', default='demande', tracking=True)

    urgence = fields.Boolean(string='Urgent', default=False)

    # ──────────────── Devise ────────────────
    company_id = fields.Many2one(related='chantier_id.company_id', store=True)
    currency_id = fields.Many2one(related='chantier_id.currency_id', store=True)
    product_uom_id = fields.Many2one(related='product_id.uom_id', string='Unité', readonly=True)
    stock_qty_available = fields.Float(string='Disponible stock', compute='_compute_supply_metrics')
    stock_virtual_available = fields.Float(string='Disponible prévisionnel', compute='_compute_supply_metrics')
    shortage_qty = fields.Float(string='Manque estimé', compute='_compute_supply_metrics')
    preferred_supplier_id = fields.Many2one('res.partner', string='Fournisseur conseillé', compute='_compute_supply_metrics')
    supplier_delay = fields.Integer(string='Délai fournisseur (jours)', compute='_compute_supply_metrics')
    availability_status = fields.Selection([
        ('en_stock', 'Disponible en stock'),
        ('previsionnel', 'Couvrable au prévisionnel'),
        ('a_commander', 'Commande requise'),
    ], string='Statut disponibilité', compute='_compute_supply_metrics')

    @api.depends('product_id', 'quantite_demandee')
    def _compute_supply_metrics(self):
        for rec in self:
            supplier = rec.product_id.seller_ids[:1]
            qty_available = rec.product_id.qty_available if rec.product_id else 0.0
            virtual_available = rec.product_id.virtual_available if rec.product_id else 0.0
            rec.stock_qty_available = qty_available
            rec.stock_virtual_available = virtual_available
            rec.preferred_supplier_id = supplier.partner_id if supplier else False
            rec.supplier_delay = int(supplier.delay or 0) if supplier else 0
            if rec.quantite_demandee <= qty_available:
                rec.availability_status = 'en_stock'
                rec.shortage_qty = 0.0
            elif rec.quantite_demandee <= virtual_available:
                rec.availability_status = 'previsionnel'
                rec.shortage_qty = max(rec.quantite_demandee - qty_available, 0.0)
            else:
                rec.availability_status = 'a_commander'
                rec.shortage_qty = max(rec.quantite_demandee - virtual_available, 0.0)

    # ──────────────── Action : Créer commande fournisseur ────────────────
    def action_creer_commande(self):
        """Créer un bon de commande fournisseur à partir de l'approvisionnement"""
        self.ensure_one()
        if self.purchase_order_id:
            raise UserError("Un bon de commande existe déjà pour cet approvisionnement.")

        # Chercher un fournisseur par défaut du produit
        supplier = self.product_id.seller_ids[:1]
        if not supplier:
            raise UserError("Aucun fournisseur défini pour ce produit. Veuillez en configurer un.")

        po = self.env['purchase.order'].create({
            'partner_id': supplier.partner_id.id,
            'origin': f'BTP/{self.chantier_id.reference}',
            'order_line': [(0, 0, {
                'product_id': self.product_id.id,
                'product_qty': self.quantite_demandee,
                'name': self.product_id.display_name,
                'price_unit': supplier.price or 0.0,
                'product_uom': self.product_id.uom_po_id.id or self.product_uom_id.id,
                'date_planned': self.date_besoin,
            })],
        })
        self.write({
            'purchase_order_id': po.id,
            'state': 'commande',
            'date_commande': fields.Date.today(),
            'date_livraison_prevue': self.date_livraison_prevue or fields.Date.add(fields.Date.today(), days=int(supplier.delay or 0)),
        })
        return {
            'name': 'Bon de commande',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': po.id,
            'view_mode': 'form',
        }

    def action_open_purchase_order(self):
        self.ensure_one()
        if not self.purchase_order_id:
            raise UserError("Aucun bon de commande n'est encore lié à cet approvisionnement.")
        return {
            'name': 'Bon de commande fournisseur',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': self.purchase_order_id.id,
            'view_mode': 'form',
        }

    @api.onchange('quantite_livree')
    def _onchange_quantite_livree(self):
        if self.quantite_livree >= self.quantite_demandee:
            self.state = 'livre'
        elif self.quantite_livree > 0:
            self.state = 'partiel'
