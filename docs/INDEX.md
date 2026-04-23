# 📚 Documentation ERP Commercial — Odoo 17 Custom Modules

**Version plateforme** : Odoo 17 Community Edition  
**Version ERP** : 2.0.0 (2025)  
**Contexte** : Entreprise BTP & Commerce — Maroc  
**Hébergement** : Azure VM (Sweden Central)  
**URL** : https://erp-btp-maroc.swedencentral.cloudapp.azure.com  

---

## 🗂️ Index des Modules

| # | Module | Fichier | Catégorie | Description courte |
|---|--------|---------|-----------|-------------------|
| 1 | `custom_sale` | [MODULE_1_VENTE.md](MODULE_1_VENTE.md) | Ventes | Commandes, devis, prévisions, workflow approbation |
| 2 | `custom_purchase` | [MODULE_2_ACHAT.md](MODULE_2_ACHAT.md) | Achats | BDC, conventions d'achat, réapprovisionnement |
| 3 | `custom_stock` | [MODULE_3_STOCK.md](MODULE_3_STOCK.md) | Stock | Contrôle qualité, projets stock, réappro. intelligent |
| 4 | `custom_accounting` | [MODULE_4_COMPTABILITE.md](MODULE_4_COMPTABILITE.md) | Comptabilité | Factures, chèques, suivi paiements, exercices fiscaux |
| 5 | `custom_hr` | [MODULE_5_RH.md](MODULE_5_RH.md) | RH | Employés Maroc (CIN/CNSS), évaluations, contrats |
| 6 | `custom_btp` | [MODULE_6_BTP.md](MODULE_6_BTP.md) | BTP | Chantiers, pointage, situations travaux, CNSS DUE |
| 7 | `custom_crm` | [MODULE_7_CRM.md](MODULE_7_CRM.md) | CRM | Leads scoring, suivi commercial, WhatsApp |
| 8 | `custom_ai` | [MODULE_8_IA.md](MODULE_8_IA.md) | IA | Assistant Mohasib (comptable BTP), OpenAI, Ollama |
| 9 | `custom_documents` | [MODULE_9_GED.md](MODULE_9_GED.md) | GED | Classement documentaire, liens cross-modules |
| 10 | `custom_dashboard` | [MODULE_10_DASHBOARD.md](MODULE_10_DASHBOARD.md) | Tableau de bord | KPI temps réel, alertes intelligentes |
| 11 | `custom_contacts` | [MODULE_11_CONTACTS.md](MODULE_11_CONTACTS.md) | Contacts | Référentiel Maroc (ICE, RC, IF, CNSS), villes |
| 12 | `custom_calendar` | [MODULE_12_CALENDRIER.md](MODULE_12_CALENDRIER.md) | Calendrier | RDV qualifiés, comptes-rendus, suivi |
| 13 | `custom_discuss` | [MODULE_13_MESSAGERIE.md](MODULE_13_MESSAGERIE.md) | Messagerie | Templates messages, notes vocales, priorités |
| 14 | `custom_whatsapp` | [MODULE_14_WHATSAPP.md](MODULE_14_WHATSAPP.md) | WhatsApp | Envoi messages, templates +212, historique |
| 15 | `custom_rbac` | [MODULE_15_RBAC.md](MODULE_15_RBAC.md) | Sécurité | Profils, règles d'accès par enregistrement |

> **Note :** Le module `custom_mohasib` (Mohasib IA legacy) est désactivé (`installable: False`).

---

## 🏗️ Architecture Globale

```
custom_btp ──────────────────────────────────────────────────────────┐
custom_accounting ────────────────────────────────────────────────── │
custom_sale ───────────┐                                             │
custom_purchase ───────┤                                             │
custom_stock ──────────┤                                             │
custom_hr ─────────────┤── custom_documents (GED)                    │
custom_crm ─────────── │                                             │
                        └── custom_ai (Mohasib IA)                   │
                                                                     │
custom_contacts ────────────────────────────────────────────────────-┘
custom_calendar ─────────────────────────────────────────────────────
custom_discuss ──────────────────────────────────────────────────────
custom_whatsapp ─────────────────────────────────────────────────────
custom_dashboard ────────────────────────────────────────────────────
custom_rbac (permissions transversales) ─────────────────────────────
```

---

## 🔧 Configuration Technique

### Déploiement Azure

| Paramètre | Valeur |
|-----------|--------|
| Groupe de ressources | `RG-ODOO-ERP` |
| VM | `vm-odoo-erp` (Ubuntu, Sweden Central) |
| IP publique | `51.107.183.143` |
| URL HTTPS | `https://erp-btp-maroc.swedencentral.cloudapp.azure.com` |
| Base de données | `odoo_erp_commercial` (PostgreSQL) |
| Conteneur Odoo | `odoo_erp_app` |
| Conteneur DB | `odoo_erp_db` |

### Devise & Localisation

| Paramètre | Valeur |
|-----------|--------|
| Pays | Maroc |
| Langue | Français (fr_MA) |
| Devise principale | MAD (Dirham marocain) |
| TVA standard | 20% |
| TVA BTP (travaux) | 14% |
| SMIG BTP horaire | 17.25 DH/h (2025) |

---

## 🔗 Flux Principaux

### Flux Vente

```
CRM (Lead) → Opportunité → Devis → Commande → Livraison → Facture → Paiement
```

### Flux Achat

```
Besoin (BTP/Stock) → Demande de prix → BDC → Réception → Contrôle qualité → Facture fournisseur
```

### Flux BTP (Facturation Chantier)

```
Chantier créé → OS démarrage → Pointages → Situations de travaux → Facture TVA 14%/20% → Paiement
```

### Flux RH

```
Recrutement → Embauche → Affectation chantier → Pointage (CNSS) → Évaluation → Fin contrat
```

---

## 📋 Modèles Principaux par Module

| Modèle Odoo | Module | Description |
|-------------|--------|-------------|
| `btp.chantier` | custom_btp | Chantier BTP |
| `btp.situation` | custom_btp | Situation de travaux |
| `btp.ressource` | custom_btp | Ressource humaine chantier |
| `btp.pointage` | custom_btp | Pointage ouvriers |
| `btp.engin` | custom_btp | Engins de chantier |
| `btp.sous.traitant` | custom_btp | Sous-traitant |
| `sale.forecast` | custom_sale | Prévision commerciale |
| `purchase.convention` | custom_purchase | Convention d'achat |
| `stock.quality.check` | custom_stock | Contrôle qualité |
| `stock.intelligent.reorder` | custom_stock | Réapprovisionnement intelligent |
| `account.cheque` | custom_accounting | Gestion des chèques |
| `account.payment.tracking` | custom_accounting | Suivi paiements |
| `hr.evaluation` | custom_hr | Évaluation employé |
| `crm.lead` (ext.) | custom_crm | Opportunité enrichie |
| `document.document` | custom_documents | Document GED |
| `whatsapp.message` | custom_whatsapp | Message WhatsApp |
| `whatsapp.template` | custom_whatsapp | Template WhatsApp |
| `dashboard.kpi` | custom_dashboard | KPI tableau de bord |
| `res.partner` (ext.) | custom_contacts | Contact Maroc |
| `res.city.morocco` | custom_contacts | Ville marocaine |

---

## 📁 Structure des Dossiers

```
custom_addons/
├── custom_accounting/     # Comptabilité & Facturation
├── custom_ai/             # Assistant IA Mohasib
├── custom_btp/            # Gestion BTP Chantiers
├── custom_calendar/       # Calendrier Avancé
├── custom_contacts/       # Contacts Maroc
├── custom_crm/            # CRM Avancé
├── custom_dashboard/      # Tableaux de Bord
├── custom_discuss/        # Messagerie Avancée
├── custom_documents/      # GED Documents
├── custom_hr/             # Ressources Humaines
├── custom_mohasib/        # [DÉSACTIVÉ] Legacy IA
├── custom_purchase/       # Achats
├── custom_rbac/           # Sécurité & Rôles
├── custom_sale/           # Ventes
├── custom_stock/          # Stock & Inventaire
└── custom_whatsapp/       # Intégration WhatsApp
```

---

*Documentation générée automatiquement depuis le code source — Version 2025*
