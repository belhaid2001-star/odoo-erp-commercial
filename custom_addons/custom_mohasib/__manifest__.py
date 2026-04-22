# -*- coding: utf-8 -*-
{
    'name': 'Mohasib - Expert Comptable IA BTP Maroc',
    'version': '17.0.2.0.0',
    'category': 'Accounting',
    'summary': 'Agent IA expert-comptable BTP Maroc : saisie NLP + conseil fiscal (TVA, IS, IR, PCM)',
    'description': """
Mohasib - Assistant Comptable IA pour le BTP Marocain
======================================================

Agent intelligent qui comprend le langage naturel du directeur BTP
et traduit automatiquement en ecritures comptables PCM.

**Mode SAISIE** : le directeur tape une phrase et Mohasib cree
l'ecriture comptable correspondante (achat materiaux, salaire,
location engin, encaissement, sous-traitance...).

**Mode CONSEIL** : le directeur pose une question fiscale et Mohasib
repond en expert (TVA BTP, IS, IR, retenues a la source, retenue
de garantie, cautions bancaires, PCM, penalites...).

Module 1 - Saisie guidee en langage naturel
Module 2 - Conseil fiscal/comptable expert BTP
Module 3 - Suivi par chantier: budget, depenses, encaissements
Module 4 - Fiscalite marocaine BTP: TVA, IS, retenues a la source
Module 5 - Paie des ouvriers BTP: SMIG, CNSS, AMO, IR
Module 6 - Alertes intelligentes
Module 7 - Rapports et etats financiers
    """,
    'author': 'ERP Commercial',
    'depends': [
        'base',
        'account',
        'analytic',
        'mail',
        'hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mohasib_pcm_data.xml',
        'data/mohasib_sequence_data.xml',
        'report/mohasib_transaction_report.xml',
        'views/mohasib_chantier_views.xml',
        'views/mohasib_conversation_views.xml',
        'views/mohasib_transaction_views.xml',
        'wizards/mohasib_saisie_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_mohasib/static/src/css/mohasib.css',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': False,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
