# -*- coding: utf-8 -*-
{
    'name': 'Gestion Commerciale - Documents',
    'version': '17.0.2.0.0',
    'category': 'Productivity',
    'summary': 'Gestion documentaire centralisée — GED liée à tous les modules',
    'description': """
        Module de gestion documentaire incluant :
        - Gestion des fichiers
        - Centralisation des documents dans une seule plateforme numérique
        - Catégorisation et recherche avancée
        - Versionnement des documents
        - Liaison directe avec BTP, Ventes, Achats, Comptabilité, RH
        - Affectation de documents existants aux dossiers spécifiques (sans re-chargement)
    """,
    'author': 'ERP Commercial',
    'depends': [
        'base',
        'mail',
        'sale_management',
        'purchase',
        'account',
        'hr',
        'custom_btp',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/document_views.xml',
        'data/document_data.xml',
        'report/documents_report_custom.xml',
        'views/menu_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
