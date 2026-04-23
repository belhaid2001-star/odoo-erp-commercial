# Module 4 : Gestion Commerciale - Comptabilité & Facturation (custom_accounting)

**Version** : 17.0.1.0.0  
**Catégorie** : Accounting  
**Dépendances** : account, account_payment  
**Plateforme** : Odoo 17 Community Edition  

---

## 1. Vue d'ensemble

Module de comptabilité et facturation avancée qui étend le module standard Odoo Accounting avec un système de relances de paiement automatisées, une gestion complète des chèques (reçus et émis), un calcul de niveau de risque client, la validation traçable des factures, des étiquettes analytiques personnalisées et l'impression de chèques.

---

## 2. Fonctionnalités détaillées

### 2.1. Gestion avancée des factures (account.move)

#### Système de relances de paiement
- **Relance envoyée** : booléen avec tracking
- **Dernière relance** : date de la dernière relance envoyée
- **Nombre de relances** : compteur incrémental
- Bouton **"Envoyer relance"** dans le header (visible uniquement pour les factures clients non payées)
- Chaque relance envoie un message au partenaire via le chatter avec :
  - Numéro de relance
  - Nom de la facture
  - Montant restant dû + devise
  - Date d'échéance
- Onglet dédié "Suivi & Relances" dans le formulaire (visible uniquement pour les factures clients)

#### Jours de retard & Niveau de risque
- **Jours de retard** : champ calculé = (aujourd'hui - date d'échéance), 0 si payée ou non échue
- **Niveau de risque** : calculé automatiquement selon des règles métier :
  - **Critique** : >90 jours de retard OU montant résiduel >100 000
  - **Élevé** : >60 jours OU montant résiduel >50 000
  - **Moyen** : >30 jours
  - **Faible** : ≤30 jours
- Badge coloré dans la vue liste et le formulaire (vert/orange/rouge)
- Colonnes optionnelles dans la vue liste des factures : Jours de retard, Niveau de risque, Nombre de relances

#### Validation traçable
- Bouton **"Valider"** réservé aux responsables comptables (group_account_manager)
- Visible uniquement pour les factures publiées non encore validées
- Enregistre automatiquement : **Validé par** (utilisateur) et **Date de validation**
- Notification dans le chatter

#### Notes & Analytique
- **Notes internes** : zone de texte pour commentaires internes sur la facture
- **Étiquettes analytiques** : champ Many2many vers le modèle custom `account.analytic.tag.custom`
- Onglet dédié "Analytique" dans le formulaire avec widget tags colorés

### 2.2. Relances automatiques (CRON)

- Job planifié `_cron_send_overdue_reminders` :
  - Recherche toutes les factures clients publiées, non payées, avec échéance dépassée
  - Envoie une relance uniquement si la dernière relance date de plus de 7 jours (hebdomadaire)
  - Entièrement automatique, sans intervention utilisateur

### 2.3. Gestion des chèques (account.cheque)

#### Modèle complet
- **Numéro de chèque** : référence unique (requis)
- **Type** : Reçu ou Émis
- **Partenaire** : client ou fournisseur
- **Montant** : en devise de la société
- **Date du chèque** et **Date d'échéance**
- **Banque** : lien vers res.bank
- **Compte bancaire** : texte libre
- **Pièce comptable** : lien vers account.move (facultatif)
- **Journal** : journal bancaire ou caisse
- **Mémo** et **Notes**

#### Workflow du chèque (6 états)
1. **Brouillon** → Bouton "Enregistrer"
2. **Enregistré** → Bouton "Déposer" ou "Retourner"
3. **Déposé** → Bouton "Compenser" ou "Retourner"
4. **Compensé** (état final positif)
5. **Retourné** (anomalie) → notification automatique dans le chatter avec montant et devise
6. **Annulé** → Bouton "Brouillon" pour réutiliser

- Barre de statut : Brouillon → Enregistré → Déposé → Compensé
- Chatter complet (messages, activités, followers)

#### Impression de chèques
- Bouton **"Imprimer"** visible uniquement pour les chèques émis
- Appelle un rapport QWeb PDF (`action_report_cheque`)
- Template d'impression professionnel avec toutes les informations

#### Vues et actions
- **Vue liste** avec couleurs conditionnelles :
  - Vert = Compensé, Rouge = Retourné, Grisé = Annulé
  - Badges colorés pour chaque état
  - Colonne Total avec somme
- **3 actions de menu** :
  - **Chèques reçus** (filtré type=received, défaut=received)
  - **Chèques émis** (filtré type=issued, défaut=issued)
  - **Tous les chèques** (sans filtre)
- Intégration dans le formulaire de facture : onglet "Chèques" avec édition inline

### 2.4. Étiquettes analytiques (account.analytic.tag.custom)

- **Nom** : libellé de l'étiquette
- **Couleur** : code couleur pour affichage visuel
- **Actif** : booléen pour archivage
- **Société** : multi-société supporté
- Vue liste éditable en inline
- Menu dédié sous Comptabilité > Analytique > Étiquettes analytiques
- Utilisables dans les factures via widget many2many_tags avec couleurs

### 2.5. Pièces justificatives sur factures

Onglet **📎 Documents** dans chaque facture pour joindre des pièces justificatives (PDF, images, etc.) :

- **Champ** : `doc_attachment_ids` (Many2many → `ir.attachment`)
- **Widget** : `many2many_binary` (glisser-déposer de fichiers)
- **Table de relation** : `account_move_doc_attachment_rel`
- Indépendant des pièces jointes techniques d'Odoo (`attachment_ids`)

### 2.6. Lien GED Documents

Onglet **📂 Documents GED** dans chaque facture pour lier des documents de la GED :

- **Champ** : `ged_linked_docs` (Many2many → `document.document`)
- **Table de relation** : `account_move_linked_doc_rel`
- Affiche : Nom, Dossier, Type, État (brouillon/validé/archivé)
- Smart button avec compteur total (documents créés + liés)

### 2.7. Suivi des paiements (account.payment.tracking)

Modèle de traçabilité des échéances et flux de trésorerie.

| Champ | Type | Description |
|-------|------|-------------|
| `name` | Char | Référence (auto-séquence) |
| `partner_id` | Many2one | Client/Fournisseur (requis) |
| `partner_type` | Selection | `client` / `fournisseur` |
| `state` | Selection | `en_attente` / `validé` / `rejeté` |

### 2.8. Exercices Fiscaux (account.fiscal.year.custom)

| Champ | Type | Description |
|-------|------|-------------|
| `name` | Char | Libellé de l'exercice (requis) |
| `date_from` / `date_to` | Date | Période |
| `state` | Selection | `ouvert` / `clôturé` |

### 2.9. Vues Stock-Comptabilité

Intégration du module stock dans la comptabilité :
- **Valorisation d'inventaire** : vue mouvements par produit/catégorie
- **Entrées/Sorties de stock** : mouvements d'inventaire valorisés
- **Produits sous le seuil** : alertes stock minimum
- **Écritures par produit** : journal des écritures liées aux mouvements de stock
- **Réconciliation stock/compta** : rapprochement stock/comptabilité

---

## 3. Modèles de données

| Modèle | Description | Type |
|--------|-------------|------|
| `account.move` | Extension des pièces comptables/factures | Héritage (_inherit) |
| `account.cheque` | Gestion complète des chèques | Nouveau modèle |
| `account.analytic.tag.custom` | Étiquettes analytiques personnalisées | Nouveau modèle |
| `account.payment.tracking` | Suivi des paiements et échéances | Nouveau modèle |
| `account.fiscal.year.custom` | Exercices fiscaux personnalisés | Nouveau modèle |

---

## 4. Onglets du Formulaire Facture

| Onglet | Contenu |
|--------|---------|
| Suivi & Relances | Bouton relance, jours retard, niveau risque |
| Chèques | Liste inline des chèques liés |
| Analytique | Étiquettes analytiques |
| Stock/Inventaire | Bons de livraison/réceptions liés |
| 📎 Documents | Pièces justificatives (upload fichiers) |
| 📂 Documents GED | Lien vers documents GED existants |

---

## 5. Sécurité / Droits d'accès

- `account.cheque` : accès CRUD pour account_user
- `account.analytic.tag.custom` : accès CRUD pour account_user
- `account.payment.tracking` : accès CRUD pour account_user
- `account.fiscal.year.custom` : accès CRUD pour account_manager
- Bouton de validation réservé au groupe `account.group_account_manager`

---

## 6. Automatisations

- **CRON relances** : envoi hebdomadaire automatique de relances pour toutes les factures en retard
- **Calcul automatique** des jours de retard et du niveau de risque à chaque modification

---

## 7. Rapports

- **Impression de chèque** : rapport QWeb PDF pour les chèques émis, prêt à l'impression physique
- **Balance âgée client** : créances classées par ancienneté (current, 30j, 60j, 90j+)
- **Grand livre** : rapport comptable standard avec filtres analytiques
