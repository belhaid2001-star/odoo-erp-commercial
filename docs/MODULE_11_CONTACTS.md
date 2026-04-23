# Module 11 : Contacts Avancés Maroc (custom_contacts)

**Version** : 17.0.1.0.0  
**Catégorie** : Contacts  
**Auteur** : ERP Commercial  
**Dépendances** : `base`, `contacts`, `mail`, `sale`, `purchase`  

---

## 1. Vue d'ensemble

Extension du module Contacts standard Odoo avec enrichissement spécifique au **contexte marocain** : numéros légaux (ICE, RC, IF, CNSS), segmentation clients, réseaux sociaux, et référentiel des villes marocaines.

---

## 2. Modèles Python

### 2.1. `res.partner` (hérité) — Contacts Enrichis

#### Champs légaux Maroc

| Champ | Type | Description |
|-------|------|-------------|
| `ice` | Char | Identifiant Commun de l'Entreprise (15 chiffres) |
| `rc` | Char | Registre du Commerce |
| `if_code` | Char | Identifiant Fiscal |
| `cnss` | Char | Numéro CNSS |
| `capital` | Float | Capital social (DH) |
| `date_creation_company` | Date | Date de création de la société |
| `morocco_city_id` | Many2one | Ville marocaine (auto-remplissage adresse) |

#### Champs de classification

| Champ | Type | Options |
|-------|------|---------|
| `contact_type_custom` | Selection | `prospect` / `client` / `fournisseur` / `partenaire` / `autre` |
| `contact_priority` | Selection | `faible` / `moyen` / `élevé` / `VIP` (défaut: moyen) |
| `segment_ids` | Many2many | Segments marketing (contact.segment) |

#### Champs de communication

| Champ | Type | Description |
|-------|------|-------------|
| `preferred_contact_method` | Selection | `email` / `téléphone` / `whatsapp` / `visite` / `courrier` |
| `linkedin` | Char | URL profil LinkedIn |
| `facebook` | Char | URL page Facebook |
| `instagram` | Char | Compte Instagram |

#### Statistiques calculées

| Champ | Type | Description |
|-------|------|-------------|
| `total_sale_amount` | Monetary | Calculé = CA total ventes |
| `sale_order_count_custom` | Integer | Calculé = nb commandes vente |
| `total_purchase_amount` | Monetary | Calculé = total achats |
| `purchase_order_count_custom` | Integer | Calculé = nb commandes fournisseur |
| `first_order_date` | Date | Calculé = date 1ère commande |
| `last_order_date` | Date | Calculé = date dernière commande |
| `internal_notes` | Html | Notes internes (non visibles par le contact) |

#### Comportements automatiques

| Méthode | Déclencheur | Action |
|---------|-------------|--------|
| `_onchange_morocco_city_id()` | Changement ville | Auto-rempli : ville, code postal, région, pays=Maroc |
| `_onchange_state_id_morocco()` | Changement région | Met à jour country_id = Maroc si région marocaine |
| `_format_phone_moroccan()` | Sauvegarde | Formate téléphone/mobile au format `+212 6XX XXX XXX` |

---

### 2.2. `contact.segment` — Segments Marketing

| Champ | Type | Description |
|-------|------|-------------|
| `name` | Char | Nom du segment (requis) |
| `description` | Text | Description |
| `color` | Integer | Couleur Kanban |
| `partner_ids` | Many2many | Contacts membres du segment |
| `partner_count` | Integer | Calculé = nb contacts |
| `active` | Boolean | Actif (défaut: Oui) |

---

### 2.3. `res.city.morocco` — Villes Marocaines

Référentiel complet des villes du Maroc.

| Champ | Type | Description |
|-------|------|-------------|
| `name` | Char | Nom de la ville (requis) |
| `zip_code` | Char | Code postal |
| `state_id` | Many2one | Région/Province marocaine |
| `country_id` | Many2one | Pays (défaut: Maroc) |
| `display_name` | Char | Calculé = `"Casablanca (20000) - Casablanca-Settat"` |

---

## 3. Vues

### Vue Formulaire Contact (héritage)

**Onglets ajoutés :**
- **Informations Maroc :** ICE, RC, IF, CNSS, capital, date création
- **Classification :** Type relation, priorité, segments
- **Communication :** Réseaux sociaux, moyen de contact préféré
- **Adresses :** Adresses de livraison et facturation multiples
- **Statistiques :** CA, nb commandes, dates premier/dernier contact

**Colonne ajoutée dans la liste :**
- Type contact (badge coloré)

---

## 4. Menus

| Menu | Action |
|------|--------|
| Contacts → Importer contacts | Import CSV de contacts |
| Contacts → Configuration → Segments | Gestion des segments marketing |
| Contacts → Rapports → Fiche contact | Rapport PDF fiche contact |

---

## 5. Données préchargées

**Configuration système :**
- Dirham marocain (MAD) défini comme devise principale
- EUR et USD comme devises secondaires actives

---

## 6. Sécurité

Hérité des droits standards des Contacts Odoo.  
Tous les utilisateurs peuvent gérer les contacts selon leur groupe.
