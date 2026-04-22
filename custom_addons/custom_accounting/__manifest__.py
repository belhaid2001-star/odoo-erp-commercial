# -*- coding: utf-8 -*-
{
    'name': 'Gestion Commerciale - Comptabilité & Facturation',
    'version': '17.0.2.0.0',
    'category': 'Accounting',
    'summary': 'Comptabilité avancée, rapprochement bancaire, analytique — lié à Stock & Inventaire',
    'description': """
        Module de comptabilité et facturation incluant :
        - Gestion des factures et paiements clients et fournisseurs
        - Gestion du rapprochement bancaire intelligent (Correspondance IA)
        - Suivi des échéances
        - Gestion de la comptabilité analytique
        - Rapport de comptabilité (Grand livre, Balance, Balance âgée, Journaux comptables)
        - Gestion des taxes avancée
        - Gestion des impressions des chèques
    """,
    'author': 'ERP Commercial',
    'depends': [
        'account',
        'account_payment',
        'stock',
        'stock_account',
        'purchase',
        'sale_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/account_analytic_views.xml',
        'views/account_dashboard_views.xml',
        'views/account_cheque_views.xml',
        'views/account_fiscal_views.xml',
        'views/account_payment_tracking_views.xml',
        'views/account_tax_report_views.xml',
        'views/account_aged_balance_views.xml',
        'data/account_data.xml',
        'report/account_report_templates.xml',
        'report/account_report_custom.xml',
        'views/menu_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
