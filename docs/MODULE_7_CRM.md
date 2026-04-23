# Module 7 : CRM Avancé (custom_crm)

**Version** : 17.0.2.0.0  
**Catégorie** : CRM  
**Auteur** : ERP Commercial  
**Dépendances** : `crm`, `sale_crm`, `calendar`, `custom_whatsapp`  

---

## 1. Vue d'ensemble

Extension du module CRM standard Odoo avec scoring de qualité des leads, suivi commercial avancé, intégration WhatsApp et Gmail, et tableaux de bord analytiques.

---

## 2. Modèles Python

### 2.1. `crm.lead` (hérité) — Opportunités & Pistes Enrichies

#### Champs personnalisés

| Champ | Type | Description |
|-------|------|-------------|
| `lead_source` | Selection | `website` / `téléphone` / `email` / `parrainage` / `réseaux_sociaux` / `événement` / `publicité` / `autre` |
| `lead_quality` | Selection | `cold` (Froid) / `warm` (Tiède) / `hot` (Chaud) — **Calculé automatiquement** |
| `estimated_closing_date` | Date | Date de clôture estimée |
| `competitor_ids` | Many2many | Concurrents identifiés (crm.competitor) |
| `loss_reason_notes` | Text | Analyse des raisons de perte |
| `next_action_description` | Text | Description de la prochaine action commerciale |
| `next_action_date` | Date | Date de la prochaine action |
| `call_count` | Integer | Nombre d'appels passés |
| `meeting_count_custom` | Integer | Calculé = nb rendez-vous (calendar.event) |
| `quote_count` | Integer | Calculé = nb devis (sale.order) |
| `conversion_rate` | Float | Calculé = `(expected_revenue × probability) / 100` |
| `last_contact_date` | Date | Date du dernier contact |
| `days_since_last_contact` | Integer | Calculé = jours depuis dernier contact |
| `internal_notes` | Html | Notes internes CRM |

#### Calcul de la qualité du lead

```python
_compute_lead_quality():
    probability >= 50%  →  'hot'  (Chaud)
    probability >= 20%  →  'warm' (Tiède)
    sinon               →  'cold' (Froid)
```

#### Boutons d'action

| Bouton | Méthode | Description |
|--------|---------|-------------|
| 📞 Enregistrer appel | `action_log_call()` | Incrémente call_count + met à jour last_contact_date + log chatter |
| 📅 Planifier RDV | `action_schedule_meeting()` | Ouvre wizard calendar.event avec contexte opportunité |
| ✉️ Gmail | `action_open_gmail_compose()` | Ouvre interface composition email Gmail |
| 💬 WhatsApp | `action_open_whatsapp_chat()` | Ouvre wizard WhatsApp avec numéro du contact |
| 📋 Devis rapide | `action_quick_quotation()` | Crée un devis sale.order lié |

#### Smart buttons (en-tête formulaire)

| Bouton | Affiche |
|--------|---------|
| RDV | Nombre de rendez-vous liés |
| Devis | Nombre de devis associés |

---

### 2.2. `crm.competitor` — Concurrents

Référentiel des entreprises concurrentes.

| Champ | Type | Description |
|-------|------|-------------|
| `name` | Char | Nom du concurrent (requis) |
| `website` | Char | Site web |
| `active` | Boolean | Actif (défaut: Oui) |
| `strength` | Text | Points forts du concurrent |
| `weakness` | Text | Points faibles |
| `notes` | Text | Notes diverses |

---

## 3. Vues principales

### Vue Formulaire Opportunité (héritage `crm.crm_lead_view_form`)

**Onglets ajoutés :**

- **Suivi commercial :**
  - Appels : call_count, last_contact_date, days_since_last_contact
  - Prochaine action : next_action_date, description
  - Concurrence : competitor_ids, loss_reason_notes

- **Notes CRM :** internal_notes (champ HTML riche)

**Colonne ajoutée dans la liste :**
- Qualité (badge coloré : rouge=Froid, orange=Tiède, vert=Chaud)
- Source
- Nb appels

### Vue Kanban (Pipeline)

Extension du kanban standard avec affichage de la qualité du lead en badge.

### Vue Recherche (héritage filtres)

**Filtres ajoutés :**
| Filtre | Condition |
|--------|-----------|
| Leads chauds | `probability >= 50` |
| Leads tièdes | `probability >= 20 AND < 50` |
| Sans contact 7j+ | `last_contact_date < today-7` |

**Groupes ajoutés :**
| Groupe | Champ |
|--------|-------|
| Source | `lead_source` |
| Qualité | `lead_quality` |
| Date clôture | `estimated_closing_date` |

---

## 4. Tableau de bord CRM

Action `action_crm_dashboard` — Vue pivot/graphique/liste des opportunités :
- Axes d'analyse : montant × étape × vendeur × probabilité
- Filtres prédéfinis : Mes opportunités, leads chauds, sans contact

---

## 5. Sécurité

| Modèle | Commercial | Manager |
|--------|------------|---------|
| `crm.competitor` | CRUD | CRUD |

**Règle d'accès (via custom_rbac) :**
- `group_commercial` : Voir uniquement ses opportunités ET celles de son équipe

---

## 6. Dépendances inter-modules

| Module | Intégration |
|--------|-------------|
| `calendar` | Planification des rendez-vous |
| `sale_crm` | Lien opportunités → devis |
| `custom_whatsapp` | Envoi messages WhatsApp depuis opportunité |
| `custom_ai` | Bouton "🤖 Assistant IA" sur formulaire opportunité |
