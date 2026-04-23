# Module 10 : Tableaux de Bord (custom_dashboard)

**Version** : 17.0.1.0.0  
**Catégorie** : Reporting  
**Auteur** : ERP Commercial  
**Dépendances** : `base`, `sale_management`, `purchase`, `stock`, `account`, `hr`, `crm`, `mail`  

---

## 1. Vue d'ensemble

Module de tableaux de bord centralisés avec interface moderne OWL (style Power BI). Agrège les données de tous les modules pour fournir une vision unifiée des KPI de l'entreprise.

---

## 2. Modèles Python

### 2.1. `dashboard.kpi` — Configuration des KPIs

| Champ | Type | Description |
|-------|------|-------------|
| `name` | Char | Nom du KPI (requis) |
| `category` | Selection | `ventes` / `achats` / `stock` / `comptabilité` / `rh` / `crm` |
| `sequence` | Integer | Ordre d'affichage (défaut: 10) |
| `active` | Boolean | Affiché (défaut: Oui) |
| `color` | Integer | Couleur de la carte KPI |
| `icon` | Char | Icône FontAwesome (défaut: `fa-bar-chart`) |
| `description` | Text | Description de la métrique |

### 2.2. Méthodes du Tableau de Bord

```python
get_full_dashboard_data(filters=None)
    → dict {
        'kpis': [...],        # Métriques calculées
        'charts': [...],      # Données graphiques
        'alerts': [...],      # Alertes intelligentes
        'today': 'JJ/MM/AAAA',
        'period_label': 'Ce mois',
        'active_filters': {...}
    }
```

#### KPIs calculés (`_dashboard_kpis`)

| KPI | Source | Description |
|-----|--------|-------------|
| Chiffre d'affaires | `account.move` factures validées | CA du mois en cours |
| Nb commandes vente | `sale.order` confirmées | Commandes de la période |
| Valeur stock | `stock.quant` | Valeur totale en entrepôt |
| Factures impayées | `account.move` en retard | Montant à encaisser |
| Nb employés actifs | `hr.employee` | Effectif courant |
| Opportunités actives | `crm.lead` | Nb leads en cours |

#### Graphiques (`_dashboard_charts`)

| Graphique | Type | Données |
|-----------|------|---------|
| Évolution CA | Courbe mensuelle sur 12 mois | account.move par mois |
| Top clients | Barres horizontales | CA par partenaire |
| Stock par catégorie | Camembert | stock.quant par categ |
| CA par vendeur | Barres | sale.order amount par user |

#### Alertes intelligentes (`_dashboard_alerts`)

| Alerte | Condition |
|--------|-----------|
| Commandes en retard | date livraison prévue < aujourd'hui |
| Stock faible | `qty_available < qty_min` (réappro.) |
| Factures impayées | `date_échéance < aujourd'hui` |
| Documents expirés | `document.is_expired = True` |
| Engins en panne | `btp.engin.state = en_panne` |

---

## 3. Filtres de Période

| Filtre | Période |
|--------|---------|
| `today` | Aujourd'hui |
| `this_week` | Cette semaine |
| `this_month` | Ce mois (défaut) |
| `this_quarter` | Ce trimestre |
| `this_year` | Cette année |
| `custom` | Personnalisé (date_from → date_to) |

---

## 4. Interface OWL (Frontend)

**Composants :**
- `dashboard_action.js` — Contrôleur OWL principal
- `custom_dashboard_templates.xml` — Templates HTML OWL
- `custom_dashboard.css` — Styles

**Fonctionnalités UI :**
- Sélecteur de période en haut
- Cartes KPI avec variation en %
- Graphiques dynamiques (Chart.js ou similar)
- Section alertes avec codes couleurs (vert/orange/rouge)
- Responsive design

---

## 5. Menus

| Menu | Description |
|------|-------------|
| **Tableaux de Bord** (racine) | Vue d'ensemble globale |
| → Vue d'ensemble | Dashboard principal |
| → Ventes → Analyse des ventes | Pivot/graphique ventes |
| → Ventes → Devis en cours | Devis en attente de confirmation |
| → Ventes → À facturer | Commandes prêtes à facturer |
| → Achats → Analyse des achats | Pivot/graphique achats |
| → Stock → Livraisons en attente | Transferts sortants |
| → Stock → Réceptions en attente | Transferts entrants |
| → Stock → Opérations en retard | Transferts dépassés |
| → Comptabilité → Factures clients impayées | Créances en retard |
| → Comptabilité → Factures fournisseurs impayées | Dettes en retard |
| → CRM → Pipeline | Opportunités par étape |
| → RH → Employés | Liste des employés actifs |

---

## 6. Sécurité

Accessible à tous les utilisateurs (`base.group_user`).  
Les données affichées respectent les règles d'accès de chaque module source.
