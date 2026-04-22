# -*- coding: utf-8 -*-
{
    'name': 'RBAC — Gestion des Accès et Profils',
    'version': '17.0.1.0.0',
    'category': 'Administration',
    'summary': 'Hiérarchie stricte des rôles : Admin, Commercial, Stock Agent, Comptable, RH Opérationnel, Gestionnaire Achats',
    'description': """
RBAC — Gestion des Accès et Permissions
=========================================
Établit une hiérarchie stricte des rôles sur toute la plateforme :

**Profils disponibles**
- Administrateur ERP : accès complet (base.group_system)
- Directeur Commercial : CRM, Ventes, Contacts, Facturation lecture
- Commercial : CRM et Ventes uniquement
- Agent de Stock : Stock et Inventaire (périmètre limité à son entrepôt)
- Comptable Maroc : Comptabilité complète sans suppression définitive
- Gestionnaire Achats : module Achats complet
- RH Opérationnel : Ressources Humaines, gestion des présences (sans salaires)
- Chef de Projet BTP : repris depuis custom_btp (Chef de chantier)

**Règles d'accès (Record Rules)**
- Agent de Stock : restreint à son entrepôt assigné
- RH Opérationnel : ne voit pas les fiches de paie
    """,
    'author': 'ERP Commercial',
    'depends': [
        'base',
        'stock',
        'account',
        'purchase',
        'sale_management',
        'hr',
        'hr_holidays',
        'crm',
        'custom_btp',
    ],
    'data': [
        'security/rbac_security.xml',
        'security/rbac_record_rules.xml',
        'security/ir.model.access.csv',
        'views/rbac_menu_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
