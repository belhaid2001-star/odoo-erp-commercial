# Module 12 : Calendrier Avancé (custom_calendar)

**Version** : 17.0.1.0.0  
**Catégorie** : Productivity  
**Auteur** : ERP Commercial  
**Dépendances** : `calendar`, `crm`  

---

## 1. Vue d'ensemble

Extension du calendrier Odoo avec qualification des rendez-vous (type, lieu, résultat), suivi post-RDV et comptes-rendus.

---

## 2. Modèles Python

### 2.1. `calendar.event` (hérité) — Événements Enrichis

#### Champs ajoutés

| Champ | Type | Options |
|-------|------|---------|
| `event_type_custom` | Selection | `réunion` / `appel` / `visite_client` / `visite_fournisseur` / `formation` / `démo` / `entretien` / `interne` / `autre` |
| `priority` | Selection | `0` Normale / `1` Basse / `2` Moyenne / `3` Haute |
| `linked_module` | Selection | `crm` / `vente` / `achat` / `stock` / `rh` / `projet` / `autre` (calculé) |
| `meeting_location_type` | Selection | `bureau` / `client` / `visioconférence` / `extérieur` |
| `meeting_url` | Char | Lien visioconférence (Zoom, Teams, Meet...) |
| `preparation_notes` | Text | Notes de préparation |
| `meeting_minutes` | Html | Compte-rendu de la réunion |
| `result` | Selection | `en_attente` (défaut) / `positif` / `neutre` / `négatif` |
| `follow_up_required` | Boolean | Suivi requis (défaut: Non) |
| `follow_up_date` | Date | Date du suivi |
| `follow_up_notes` | Text | Notes du suivi |

#### Méthodes

| Méthode | Description |
|---------|-------------|
| `action_mark_positive()` | Marque le RDV comme positif |
| `action_mark_negative()` | Marque le RDV comme négatif |
| `action_request_follow_up()` | Active follow_up_required + message dans chatter |
| `_compute_linked_module()` | Déduit le module lié (si opportunity_id → crm) |

---

## 3. Types de Rendez-vous (Données)

Types préconfigurés dans le système :
- Réunion de travail
- Appel téléphonique
- Visite client
- Visite fournisseur
- Formation
- Démonstration

---

## 4. Vues

### Vue Formulaire (héritage `calendar.view_calendar_event_form`)

**Onglets ajoutés :**
- **Détails :** Type RDV, lieu, priorité
- **Visioconférence :** Lien meeting_url
- **Préparation :** preparation_notes
- **Résultat :** Résultat (positif/neutre/négatif), suivi requis/date/notes
- **Compte-rendu :** Éditeur HTML meeting_minutes

---

## 5. Menus

| Menu | Action |
|------|--------|
| Calendrier → Configuration → Types de rendez-vous | Gestion des catégories de RDV |
| Calendrier → Rapports → Rapport de réunion | Export PDF des réunions |

---

## 6. Rapport PDF

**Rapport réunion** (`calendar_report_custom`) :
- Liste des réunions de la période avec participants
- Format imprimable pour archivage
