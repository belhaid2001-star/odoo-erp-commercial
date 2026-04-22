# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DocumentFolder(models.Model):
    _name = 'document.folder'
    _description = 'Dossier de documents'
    _order = 'sequence, name'
    _parent_name = 'parent_id'

    name = fields.Char(string='Nom du dossier', required=True)
    sequence = fields.Integer(string='Séquence', default=10)
    parent_id = fields.Many2one(
        'document.folder',
        string='Dossier parent',
        ondelete='cascade',
    )
    child_ids = fields.One2many(
        'document.folder',
        'parent_id',
        string='Sous-dossiers',
    )
    document_ids = fields.One2many(
        'document.document',
        'folder_id',
        string='Documents',
    )
    document_count = fields.Integer(
        string='Nombre de documents',
        compute='_compute_document_count',
    )
    description = fields.Text(string='Description')
    color = fields.Integer(string='Couleur')
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)

    def _compute_document_count(self):
        for folder in self:
            folder.document_count = len(folder.document_ids)


class DocumentDocument(models.Model):
    _name = 'document.document'
    _description = 'Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Nom du document', required=True, tracking=True)
    folder_id = fields.Many2one(
        'document.folder',
        string='Dossier',
        required=True,
        tracking=True,
    )

    file = fields.Binary(
        string='Fichier',
        attachment=True,
        required=True,
    )
    file_name = fields.Char(string='Nom du fichier')
    file_size = fields.Integer(
        string='Taille (octets)',
        compute='_compute_file_size',
    )

    document_type = fields.Selection([
        ('contract', 'Contrat'),
        ('invoice', 'Facture'),
        ('report', 'Rapport'),
        ('policy', 'Politique'),
        ('procedure', 'Procédure'),
        ('template', 'Modèle'),
        ('correspondence', 'Correspondance'),
        ('certificate', 'Certificat'),
        ('other', 'Autre'),
    ], string='Type de document', default='other', tracking=True)

    color = fields.Integer(string='Couleur')

    partner_id = fields.Many2one(
        'res.partner',
        string='Partenaire lié',
    )

    tag_ids = fields.Many2many(
        'document.tag',
        string='Étiquettes',
    )

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('validated', 'Validé'),
        ('archived', 'Archivé'),
    ], string='État', default='draft', tracking=True)

    version = fields.Integer(
        string='Version',
        default=1,
    )

    expiration_date = fields.Date(
        string='Date d\'expiration',
    )

    is_expired = fields.Boolean(
        string='Expiré',
        compute='_compute_is_expired',
        store=True,
    )

    responsible_id = fields.Many2one(
        'res.users',
        string='Responsable',
        default=lambda self: self.env.user,
        tracking=True,
    )

    notes = fields.Text(string='Notes')

    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company,
    )

    # ──────────────── Liaisons cross-modules (GED centralisée) ────────────────
    chantier_id = fields.Many2one(
        'btp.chantier',
        string='Chantier BTP',
        ondelete='set null',
        help="Affecter ce document à un chantier BTP.",
    )
    sale_id = fields.Many2one(
        'sale.order',
        string='Bon de commande vente',
        ondelete='set null',
        help="Affecter ce document à un devis/bon de commande client.",
    )
    purchase_id = fields.Many2one(
        'purchase.order',
        string='Commande fournisseur',
        ondelete='set null',
        help="Affecter ce document à une commande fournisseur.",
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Facture / Écriture comptable',
        ondelete='set null',
        help="Affecter ce document à une facture ou écriture comptable.",
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employé',
        ondelete='set null',
        help="Affecter ce document au dossier RH d'un employé.",
    )

    # --- Calculs ---
    def _compute_file_size(self):
        for doc in self:
            if doc.file:
                doc.file_size = len(doc.file) if isinstance(doc.file, bytes) else 0
            else:
                doc.file_size = 0

    @api.depends('expiration_date')
    def _compute_is_expired(self):
        today = fields.Date.today()
        for doc in self:
            doc.is_expired = doc.expiration_date and doc.expiration_date < today

    # --- Actions ---
    def action_validate(self):
        self.write({'state': 'validated'})
        for doc in self:
            doc.message_post(
                body=_("Document validé par %s") % self.env.user.name,
                subtype_xmlid='mail.mt_note',
            )

    def action_archive(self):
        self.write({'state': 'archived'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_new_version(self):
        """Créer une nouvelle version du document"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nouvelle version de %s') % self.name,
            'res_model': 'document.document',
            'view_mode': 'form',
            'context': {
                'default_name': self.name,
                'default_folder_id': self.folder_id.id,
                'default_document_type': self.document_type,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
                'default_version': self.version + 1,
                'default_tag_ids': [(6, 0, self.tag_ids.ids)],
            },
        }


class DocumentTag(models.Model):
    _name = 'document.tag'
    _description = 'Étiquette de document'

    name = fields.Char(string='Nom', required=True)
    color = fields.Integer(string='Couleur')
    active = fields.Boolean(default=True)
