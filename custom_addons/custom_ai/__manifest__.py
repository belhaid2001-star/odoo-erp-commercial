# -*- coding: utf-8 -*-
{
    'name': 'Mohasib — Expert-Comptable IA BTP',
    'version': '17.0.2.0.0',
    'category': 'Extra Tools',
    'summary': 'Mohasib : Expert-comptable IA spécialisé BTP Maroc — PCM, TVA, IS, IR, écritures comptables',
    'description': """
Mohasib — Expert-Comptable IA BTP
====================================
* Assistant IA expert-comptable marocain spécialisé BTP
* Double mode : CONSEIL fiscal et SAISIE COMPTABLE (PCM)
* Détection d'intention automatique (question → conseil, opération → écriture)
* Plan Comptable Marocain : TVA 20%, IS, IR, retenues à la source
* Analyse financière par chantier (marge, retard, pénalités)
* Fonctionne en mode autonome (règles) ou avec API OpenAI/Ollama
    """,
    'author': 'ERP Commercial',
    'depends': [
        'base',
        'mail',
        'sale_management',
        'purchase',
        'stock',
        'account',
        'hr',
        'crm',
        'custom_btp',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/ai_config_views.xml',
        'views/ai_wizard_views.xml',
        'views/ai_buttons_views.xml',
        'views/menu_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
