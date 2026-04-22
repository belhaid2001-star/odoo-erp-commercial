# -*- coding: utf-8 -*-
{
    'name': 'Gestion des Contacts Avancée',
    'version': '17.0.1.0.0',
    'category': 'Contacts',
    'summary': 'Gestion avancée du portefeuille de contacts et adresses',
    'description': """
Gestion des Contacts - ERP Commercial
=======================================
* Portefeuille de contacts enrichi
* Segmentation et catégorisation avancée
* Gestion multi-adresses
* Suivi de la relation client
* Statistiques et rapports contacts
    """,
    'author': 'ERP Commercial',
    'depends': [
        'base',
        'contacts',
        'mail',
        'sale',
        'purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/morocco_regions_cities.xml',
        'data/system_config.xml',
        'wizard/contact_import_wizard_views.xml',
        'views/partner_views.xml',
        'data/contact_data.xml',
        'report/contacts_report_custom.xml',
        'views/menu_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
