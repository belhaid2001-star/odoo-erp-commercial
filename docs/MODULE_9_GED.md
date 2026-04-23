# Module 9 : Gestion Documentaire — GED (custom_documents)

**Version** : 17.0.2.0.0  
**Catégorie** : Document Management  
**Auteur** : ERP Commercial  
**Dépendances** : `base`, `mail`, `sale_management`, `purchase`, `account`, `hr`, `custom_btp`  

---

## 1. Vue d'ensemble

Module de Gestion Électronique de Documents (GED) centralisé. Permet d'archiver, classifier et retrouver tous les documents de l'entreprise, avec liens directs vers les chantiers, ventes, achats, factures et employés.

**Fonctionnalités :**
- Classement hiérarchique par dossiers
- Étiquetage et catégorisation
- Workflow de validation (brouillon → validé → archivé)
- Détection automatique des documents expirés
- Liaison cross-modules (BTP, Ventes, Achats, Comptabilité, RH)
- Onglet GED dans les formulaires des modules liés
- Bouton smart button sur chaque module lié

---

## 2. Modèles Python

### 2.1. `document.folder` — Dossiers

Structure hiérarchique de classement.

| Champ | Type | Description |
|-------|------|-------------|
| `name` | Char | Nom du dossier (requis) |
| `sequence` | Integer | Ordre d'affichage (défaut: 10) |
| `parent_id` | Many2one | Dossier parent (hiérarchie, cascade) |
| `child_ids` | One2many | Sous-dossiers |
| `document_ids` | One2many | Documents dans ce dossier |
| `document_count` | Integer | Calculé = nb documents |
| `description` | Text | Description |
| `color` | Integer | Couleur Kanban |
| `active` | Boolean | Actif (défaut: Oui) |

**Dossiers par défaut (installés au déploiement) :**
- Général (ID 1)
- Contrats (ID 2)
- RH (ID 3)
- Finance (ID 4)
- Juridique (ID 5)

---

### 2.2. `document.document` — Documents

Modèle principal des documents avec gestion de versions.

| Champ | Type | Description |
|-------|------|-------------|
| `name` | Char | Nom du document (requis, suivi) |
| `folder_id` | Many2one | Dossier de classement (requis, suivi) |
| `file` | Binary | Fichier joint (requis, `attachment=True`) |
| `file_name` | Char | Nom du fichier |
| `file_size` | Integer | Calculé = taille en octets |
| `document_type` | Selection | `contrat` / `facture` / `rapport` / `politique` / `procédure` / `modèle` / `correspondance` / `certificat` / `autre` |
| `partner_id` | Many2one | Partenaire associé (optionnel) |
| `tag_ids` | Many2many | Étiquettes (`document.tag`) |
| `state` | Selection | `brouillon` / `validé` / `archivé` (suivi) |
| `version` | Integer | Version du document (défaut: 1) |
| `expiration_date` | Date | Date d'expiration |
| `is_expired` | Boolean | Calculé — `True` si `expiration_date < aujourd'hui` |
| `responsible_id` | Many2one | Responsable (défaut: utilisateur courant, suivi) |
| `notes` | Text | Notes libres |

**Liens cross-modules :**
| Champ | Type | Lien |
|-------|------|------|
| `chantier_id` | Many2one | btp.chantier |
| `sale_id` | Many2one | sale.order |
| `purchase_id` | Many2one | purchase.order |
| `invoice_id` | Many2one | account.move |
| `employee_id` | Many2one | hr.employee |

**Étiquettes par défaut :**
- Important
- Urgent
- Confidentiel
- À signer
- À archiver

**Documents de démonstration :**

| Document | Dossier | Catégorie |
|----------|---------|-----------|
| Contrat sous-traitant BTP | Contrats | Contrat |
| Devis chantier 2024 | Contrats | Rapport |
| Facture Holcim Ciment | Finance | Facture |
| Attestation CNSS | RH | Certificat |
| Registre de commerce | Juridique | Certificat |
| Plan sécurité HSE | Général | Procédure |

---

### 2.3. `document.tag` — Étiquettes de Documents

| Champ | Type | Description |
|-------|------|-------------|
| `name` | Char | Libellé de l'étiquette (requis) |
| `color` | Integer | Couleur |

---

### 2.4. Relations Cross-modules (`document_relations.py`)

Extension des modèles pour accéder à la GED depuis chaque module.

#### `account.move` (Factures)

| Champ | Type | Description |
|-------|------|-------------|
| `ged_document_ids` | One2many | Documents créés depuis cette facture (via `invoice_id`) |
| `ged_linked_docs` | Many2many | Documents GED existants liés (relation `account_move_linked_doc_rel`) |
| `ged_document_count` | Integer | Calculé = `len(ged_document_ids) + len(ged_linked_docs)` |

#### `sale.order`, `purchase.order`, `hr.employee`

Chacun possède `ged_document_ids` (One2many) et `ged_document_count`.

---

## 3. Vues

### Vue Documents (Kanban)

Groupement par état — Brouillon / Validé / Archivé.  
Affichage : icône type, étiquettes, date expiration (rouge si expiré).

### Vue Documents (Liste)

Colonnes : Nom, Dossier, Type, État, Responsable, Date création.  
Filtres : Par état, par type, par dossier, par expiration.

### Vue Dossiers (Arborescence)

Liste hiérarchique avec compteur de documents par dossier.

### Smart buttons & onglets intégrés aux modules

| Module | Smart button | Onglet GED |
|--------|-------------|-----------|
| Factures | ✅ (ged_document_count) | ✅ (ged_linked_docs) |
| Commandes vente | ✅ (ged_document_count) | ✅ |
| Commandes fournisseur | ✅ (ged_document_count) | ✅ |
| Employés | ✅ (ged_document_count) | ✅ |

---

## 4. Menus

| Menu | Action |
|------|--------|
| Documents (racine) | — |
| Documents → GED — Tous les documents | Vue liste/kanban de tous les documents |
| Documents → Dossiers | Arborescence des dossiers |
| Documents → Pièces jointes → Toutes | Tous les attachments Odoo |
| Documents → Pièces jointes → Par Chantier BTP | Filtré par chantier |
| Documents → Pièces jointes → Par Commande Vente | Filtré par order |

---

## 5. Sécurité

| Modèle | Accès |
|--------|-------|
| `document.folder` | Tous utilisateurs (CRUD) |
| `document.document` | Tous utilisateurs (CRUD) |
| `document.tag` | Tous utilisateurs (CRUD) |
