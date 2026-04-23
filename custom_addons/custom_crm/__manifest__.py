# -*- coding: utf-8 -*-
{
    'name': 'Gestion Commerciale - CRM',
    'version': '17.0.2.0.0',
    'category': 'Sales/CRM',
    'summary': 'CRM avancé - pistes, opportunités, pipelines, activités',
    'description': """
        Module CRM incluant :
        - Suivi des pistes et des opportunités
        - Planification des appels et des rendez-vous
        - Planification des activités suivantes
        - Synchronisation des emails et messages avec les pipelines
        - Création rapide de devis
    """,
    'author': 'ERP Commercial',
    'depends': [
        'crm',
        'sale_crm',
        'calendar',
        'custom_whatsapp',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/crm_data.xml',
        'views/crm_lead_views.xml',
        'views/crm_dashboard_views.xml',
        'report/crm_report_custom.xml',
        'views/menu_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
    'license': 'LGPL-3',
}
