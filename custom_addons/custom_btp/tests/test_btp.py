# -*- coding: utf-8 -*-
"""
===========================================================================
  TEST BTP — Tests ciblés sur les intégrations chantier / météo / achats
===========================================================================
"""
from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'custom_btp')
class TestBtpCustom(TransactionCase):
    """Tests du lot de modifications BTP."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Client Chantier Test'})
        cls.supplier = cls.env['res.partner'].create({'name': 'Fournisseur BTP Test'})
        cls.user = cls.env.ref('base.user_admin')
        cls.chantier = cls.env['btp.chantier'].create({
            'name': 'Chantier Test',
            'maitre_ouvrage_id': cls.partner.id,
            'responsable_id': cls.user.id,
            'type_marche': 'prive',
        })
        cls.other_chantier = cls.env['btp.chantier'].create({
            'name': 'Autre Chantier',
            'maitre_ouvrage_id': cls.partner.id,
            'responsable_id': cls.user.id,
            'type_marche': 'prive',
        })
        cls.lot = cls.env['btp.lot'].create({
            'name': 'Gros oeuvre',
            'chantier_id': cls.chantier.id,
            'responsable_id': cls.user.id,
        })
        cls.other_lot = cls.env['btp.lot'].create({
            'name': 'Lot externe',
            'chantier_id': cls.other_chantier.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Ciment C25',
            'type': 'consu',
        })
        cls.env['product.supplierinfo'].create({
            'partner_id': cls.supplier.id,
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'price': 85.0,
            'delay': 4,
        })

    def test_01_task_syncs_to_project_task(self):
        """Chaque tâche BTP crée une tâche projet globale synchronisée."""
        task = self.env['btp.tache'].create({
            'name': 'Préparer le béton',
            'lot_id': self.lot.id,
            'responsable_id': self.user.id,
            'date_fin': date.today() + timedelta(days=2),
        })
        self.assertTrue(task.project_task_id)
        self.assertEqual(task.project_task_id.project_id, self.chantier.project_id)
        self.assertEqual(task.project_task_id.user_ids, self.user)

        task.write({'name': 'Préparer le béton armé'})
        self.assertEqual(task.project_task_id.name, 'Préparer le béton armé')

    def test_02_meteo_requires_consistent_links(self):
        """Une météo ne peut pas pointer vers un lot d'un autre chantier."""
        with self.assertRaises(ValidationError):
            self.env['btp.meteo'].create({
                'date': date.today(),
                'chantier_id': self.chantier.id,
                'lot_id': self.other_lot.id,
                'description': 'Pluie',
            })

    def test_03_appro_supply_metrics_and_po(self):
        """L'approvisionnement remonte stock/fournisseur et crée un PO fournisseur."""
        appro = self.env['btp.approvisionnement'].create({
            'chantier_id': self.chantier.id,
            'lot_id': self.lot.id,
            'product_id': self.product.id,
            'quantite_demandee': 12.0,
            'date_besoin': date.today() + timedelta(days=3),
        })
        self.assertEqual(appro.preferred_supplier_id, self.supplier)
        self.assertEqual(appro.supplier_delay, 4)
        self.assertEqual(appro.availability_status, 'a_commander')
        self.assertEqual(appro.shortage_qty, 12.0)

        result = appro.action_creer_commande()
        self.assertEqual(result.get('res_model'), 'purchase.order')
        self.assertTrue(appro.purchase_order_id)
        self.assertEqual(appro.purchase_order_id.partner_id, self.supplier)
        self.assertEqual(appro.state, 'commande')
