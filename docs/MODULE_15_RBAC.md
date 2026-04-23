# Module 15 : Gestion des Rôles et Permissions — RBAC (custom_rbac)

**Version** : 17.0.1.0.0  
**Catégorie** : Administration  
**Auteur** : ERP Commercial  
**Dépendances** : `base`, `stock`, `account`, `purchase`, `sale_management`, `hr`, `hr_holidays`, `crm`, `custom_btp`  

---

## 1. Vue d'ensemble

Module de définition des profils de sécurité (rôles) et règles d'accès au niveau des enregistrements. Implémente une hiérarchie stricte de permissions conforme aux besoins d'une entreprise BTP/Commerce marocaine.

---

## 2. Groupes / Profils Définis

### 2.1. `group_erp_admin` — Administrateur ERP

- **Catégorie :** Administration
- **Droits :** Accès complet à tous les modules
- **Héritage :** `base.group_system` (super-admin implied)

---

### 2.2. `group_directeur_commercial` — Directeur Commercial

- **Catégorie :** Ventes/CRM
- **Accès :**
  - CRM : lecture + écriture complète (toutes opportunités)
  - Ventes : lecture + écriture + validation commandes
  - Contacts : accès complet
  - Comptabilité : lecture des factures
  - Rapports : tous les rapports ventes/CRM

---

### 2.3. `group_commercial` — Commercial

- **Catégorie :** Ventes/CRM
- **Accès :**
  - CRM : uniquement ses propres opportunités et celles de son équipe
  - Ventes : création et modification (pas de suppression)
  - Contacts : lecture + écriture
- **Restriction (Record Rule) :** Limité à ses propres leads + leads de son équipe commerciale

---

### 2.4. `group_stock_agent` — Agent de Stock

- **Catégorie :** Stock/Inventaire
- **Accès :**
  - Stock : transferts, réceptions, expéditions
  - Inventaire : ajustements de stock
- **Restriction (Record Rule) :** Limité à son entrepôt assigné

---

### 2.5. `group_comptable` — Comptable Maroc

- **Catégorie :** Comptabilité
- **Accès :**
  - Comptabilité : accès complet (journaux, écritures, paiements)
  - Chèques : gestion complète
  - Rapports fiscaux : TVA, grand-livre, balance âgée
- **Restriction (Record Rule) :** Interdit de supprimer des écritures validées (`state = posted`)

---

### 2.6. `group_gestionnaire_achats` — Gestionnaire Achats

- **Catégorie :** Achats
- **Accès :**
  - Achats : accès complet (BDC, conventions, fournisseurs)
  - Stock : réceptions fournisseurs
  - Comptabilité : lecture des factures fournisseurs

---

### 2.7. `group_rh_operationnel` — RH Opérationnel

- **Catégorie :** Ressources Humaines
- **Accès :**
  - Employés : lecture + écriture (pas de suppression)
  - Congés : gestion des demandes
  - Évaluations : création et modification
- **Restriction :** Ne voit pas les fiches de paie

---

## 3. Règles d'Accès (Record Rules)

### `rule_stock_picking_agent`

```
Modèle     : stock.picking
Groupe     : group_stock_agent
Condition  : (aucune restriction d'affichage)
Droits     : Lecture ✓  Écriture ✓  Création ✓  Suppression ✗
Effet      : L'agent peut travailler avec les transferts mais ne peut pas les supprimer
```

---

### `rule_account_move_comptable_no_delete`

```
Modèle     : account.move
Groupe     : group_comptable
Condition  : state != 'posted' (brouillon/annulé uniquement)
Droits     : Lecture ✓  Écriture ✓  Création ✓  Suppression ✓ (brouillon seulement)
Effet      : Le comptable ne peut pas supprimer les écritures déjà validées (posted)
```

---

### `rule_crm_lead_commercial`

```
Modèle     : crm.lead
Groupe     : group_commercial
Condition  : lead.user_id = user.id
             OU lead.team_id IN user.sale_team_id
Droits     : Lecture ✓  Écriture ✓  Création ✓  Suppression ✗
Effet      : Le commercial ne voit que ses propres opportunités et celles de son équipe
```

---

## 4. Vue Administrative

### Menu RBAC

| Menu | Action |
|------|--------|
| Configuration → RBAC → Rôles & Permissions | Liste des groupes et accès |

---

## 5. Tableau Récapitulatif des Droits

| Module | Admin ERP | Directeur Com. | Commercial | Comptable | Agent Stock | Gest. Achats | RH Opérat. |
|--------|-----------|----------------|------------|-----------|-------------|--------------|------------|
| CRM | ✅ CRUD | ✅ CRUD | 🔒 Équipe | ❌ | ❌ | ❌ | ❌ |
| Ventes | ✅ CRUD | ✅ CRUD | ✅ CRU | ❌ | ❌ | ❌ | ❌ |
| Achats | ✅ CRUD | 👁 Lecture | ❌ | 👁 Lecture | ❌ | ✅ CRUD | ❌ |
| Stock | ✅ CRUD | ❌ | ❌ | ❌ | ✅ CRU | ✅ CRU | ❌ |
| Comptabilité | ✅ CRUD | 👁 Lecture | ❌ | ✅ CRUD | ❌ | 👁 Lecture | ❌ |
| RH | ✅ CRUD | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ CRU |
| BTP | ✅ CRUD | 👁 Lecture | ❌ | ✅ Situations | ❌ | ✅ Approvisionnements | ❌ |

**Légende :** CRUD=Créer+Lire+Modifier+Supprimer | CRU=sans Suppression | 👁=Lecture seule | 🔒=Limité | ❌=Aucun accès
