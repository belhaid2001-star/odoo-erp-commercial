# -*- coding: utf-8 -*-
{
    'name': 'BTP Chantiers - Gestion Complète des Chantiers BTP Maroc',
    'version': '17.0.2.0.0',
    'category': 'Project',
    'summary': 'Gestion complète des chantiers BTP au Maroc : lots, tâches, pointage, engins, situations, sous-traitants, CNSS',
    'description': """
Module custom_btp — Gestion Complète des Chantiers BTP Maroc
============================================================

Module complet de gestion de chantiers BTP adapté au contexte marocain :

**Chantiers & Lots**
- Gestion complète du cycle de vie du chantier (étude → clôture)
- Lots avec suivi budgétaire en temps réel
- Tâches hiérarchiques avec dépendances

**Ressources & Pointage**
- Registre du personnel chantier (CIN, CNSS, qualification)
- Pointage journalier avec géolocalisation
- Calcul automatique heures supplémentaires (SMIG +25%/+50%/+100%)

**Engins & Maintenance**
- Suivi du parc engins (pelle, grue, bétonnière...)
- Pointage engins avec consommation gasoil
- Alertes assurance et visite technique

**Financier**
- Situations de travaux avec cumuls
- Retenue de garantie, TVA marocaine (20%/14%)
- Révision des prix (formule P=P0×(0.15+0.85×BT/BT0))
- Génération automatique de factures

**Sous-traitance**
- Gestion des sous-traitants avec documents légaux
- Conformité RC/Patente/IF/ICE/CNSS

**Réceptions**
- PV de réception provisoire/définitive
- Gestion des réserves avec suivi de levée

**Rapports Marocains**
- Situation de travaux (format standard)
- Décompte quantitatif
- PV de réception
- Registre du personnel (obligatoire — Inspection du Travail)
- Fiche pointage hebdomadaire
- Bordereau CNSS (format DUE)

**API REST**
- POST /api/btp/pointage — Pointage mobile
- GET /api/btp/chantier/<id>/dashboard — KPI chantier

**Wizards**
- Génération situation de travaux
- Export CNSS format DUE
- Clôture chantier avec vérifications
    """,
    'author': 'ERP Commercial',
    'depends': [
        'base',
        'project',
        'hr',
        'hr_contract',
        'purchase',
        'stock',
        'account',
        'mail',
        'custom_hr',
        'custom_documents',
    ],
    'data': [
        # Sécurité
        'security/btp_security.xml',
        'security/ir.model.access.csv',
        # Données
        'data/btp_sequence_data.xml',
        'data/btp_feries_data.xml',
        'data/btp_config_data.xml',
        # Rapports
        'report/btp_reports.xml',
        'report/btp_cnss_report.xml',
        # Vues
        'views/btp_chantier_views.xml',
        'views/btp_lot_tache_views.xml',
        'views/btp_ressource_pointage_views.xml',
        'views/btp_engin_views.xml',
        'views/btp_situation_appro_views.xml',
        'views/btp_other_views.xml',
        'views/btp_dashboard_views.xml',
        # Wizards
        'wizards/btp_wizard_views.xml',
        # Menus
        'views/menu_views.xml',
    ],
    'demo': [
        'data/btp_demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_btp/static/src/css/btp.css',
            'custom_btp/static/src/css/btp_dashboard.css',
            'custom_btp/static/src/xml/btp_dashboard_templates.xml',
            'custom_btp/static/src/js/btp_dashboard_action.js',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
