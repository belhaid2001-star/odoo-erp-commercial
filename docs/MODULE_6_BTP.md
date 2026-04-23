# Module 6 : Gestion BTP — Chantiers BTP Maroc (custom_btp)

**Version** : 17.0.2.0.0  
**Catégorie** : Project  
**Auteur** : ERP Commercial  
**Dépendances** : `base`, `project`, `hr`, `hr_contract`, `purchase`, `stock`, `account`, `mail`, `custom_hr`  

---

## 1. Vue d'ensemble

Module de gestion complète de chantiers BTP adapté au **contexte marocain**. Il couvre l'intégralité du cycle de vie d'un chantier, de la phase d'étude jusqu'à la clôture définitive.

**Fonctionnalités clés :**
- Gestion du cycle de vie complet (étude → réception définitive → clôture)
- Ressources humaines avec pointage et géolocalisation GPS
- Gestion des engins et maintenance
- Situations de travaux avec TVA marocaine (20%/14%)
- Sous-traitance avec contrôle des documents légaux (RC, Patente, IF, ICE, CNSS)
- Réceptions provisoires/définitives avec gestion des réserves
- Export CNSS au format DUE
- Révision des prix pour marchés publics
- API REST pour pointage mobile

---

## 2. Modèles Python

### 2.1. `btp.chantier` — Chantier BTP (Modèle principal)

Modèle central représentant un chantier BTP avec gestion complète.

#### États (workflow)

```
étude → appel_offres → attribué → ordre_service → en_cours
                                                      ↓
                                                   [arrêt] ↔ [reprise]
                                                      ↓
                                              réception_provisoire
                                                      ↓
                                              levée_réserves
                                                      ↓
                                              réception_définitive
                                                      ↓
                                                   clôture
```

#### Champs principaux

| Champ | Type | Réq. | Description |
|-------|------|------|-------------|
| `name` | Char | ✓ | Nom du chantier |
| `reference` | Char | | Référence unique (auto-générée) |
| `type_marche` | Selection | ✓ | `prive` / `public` / `bon_commande` |
| `state` | Selection | ✓ | État du chantier (11 états, voir workflow) |
| `montant_contrat` | Monetary | | Montant du contrat en DH |
| `montant_avenant` | Monetary | | Avenants cumulés |
| `montant_total` | Monetary | Calculé | `montant_contrat + montant_avenant` |
| `taux_retenue_garantie` | Selection | | 5% ou 10% (défaut: 5%) |
| `montant_retenue` | Monetary | Calculé | `montant_total × taux_retenue / 100` |
| `date_debut_prev` / `date_fin_prev` | Date | | Dates prévisionnelles |
| `date_debut_reel` / `date_fin_reel` | Date | | Dates réelles |
| `duree_prev_jours` | Integer | Calculé | Durée prévisionnelle en jours |
| `retard_jours` | Integer | Calculé | Retard = `date_fin_reel - date_fin_prev` |
| `taux_avancement` | Float (%) | Calculé | Avancement global depuis situations validées |
| `penalite_retard` | Monetary | Calculé | Pénalité si retard (contrats publics) |
| `indice_bt_base` / `indice_bt_actuel` | Float | | Pour révision des prix marchés publics |
| `maitre_ouvrage_id` | Many2one | | Maître d'ouvrage (client) |
| `maitre_oeuvre_id` | Many2one | | Maître d'œuvre |
| `architecte_id` / `bureau_controle_id` | Many2one | | Intervenants |
| `responsable_id` | Many2one | ✓ | Chef de projet responsable |
| `adresse_chantier` | Text | | Adresse complète |
| `coordonnees_gps` | Char | | Format: `"47.5°N,122.3°W"` |
| `taux_consommation_global` | Float | Calculé | Moyenne pondérée des lots |

#### Relations

| Relation | Type | Modèle cible |
|----------|------|--------------|
| `lot_ids` | One2many | btp.lot |
| `tache_ids` | One2many | btp.tache |
| `situation_ids` | One2many | btp.situation |
| `reception_ids` | One2many | btp.reception |
| `engin_ids` | One2many | btp.engin |
| `pointage_ids` | One2many | btp.pointage |
| `reunion_ids` | One2many | btp.reunion |
| `meteo_ids` | One2many | btp.meteo |
| `approvisionnement_ids` | One2many | btp.approvisionnement |
| `sous_traitant_ids` | Many2many | btp.sous.traitant |
| `ressource_ids` | Many2many | btp.ressource |

#### Boutons d'action

| Bouton | Méthode | Transition état |
|--------|---------|-----------------|
| Appel d'offres | `action_appel_offres()` | étude → appel_offres |
| Attribuer | `action_attribuer()` | appel_offres → attribué |
| Ordre de service | `action_ordre_service()` | attribué → ordre_service |
| Démarrer | `action_demarrer()` | ordre_service → en_cours |
| Arrêter | `action_arreter()` | en_cours → arrêt |
| Reprendre | `action_reprendre()` | arrêt → en_cours |
| Réception provisoire | `action_reception_provisoire()` | en_cours → reception_prov |
| Réception définitive | `action_reception_definitive()` | levee_reserves → reception_def |
| Clôturer | `action_cloturer()` | reception_def → cloture |
| Calculer révision prix | `calculer_revision_prix()` | Formule P = P0 × (0.15 + 0.85 × BT/BT0) |

---

### 2.2. `btp.lot` — Lots de Chantier

Découpage d'un chantier en lots budgétaires.

| Champ | Type | Description |
|-------|------|-------------|
| `name` | Char | Nom du lot (requis) |
| `chantier_id` | Many2one | Chantier parent (requis, cascade) |
| `budget_prevu` | Monetary | Budget alloué |
| `cout_reel` | Monetary | Calculé = Σ montants situations validées |
| `ecart` | Monetary | Calculé = `budget_prevu - cout_reel` |
| `taux_consommation` | Float (%) | Calculé = `(cout_reel / budget_prevu) × 100` |
| `responsable_id` | Many2one | Chef de lot |

---

### 2.3. `btp.tache` — Tâches Hiérarchiques

Structure hiérarchique des tâches avec synchronisation projet Odoo.

| Champ | Type | Description |
|-------|------|-------------|
| `lot_id` | Many2one | Lot parent (requis, cascade) |
| `parent_id` / `child_ids` | Many2one/One2many | Hiérarchie (tâche parente/sous-tâches) |
| `state` | Selection | `planifié` / `en_cours` / `bloqué` / `terminé` |
| `priorite` | Selection | `normale` / `urgente` / `critique` |
| `date_debut` / `date_fin` | Date | Planning |
| `avancement` | Float (%) | Avancement saisi manuellement (0-100) |
| `duree_reelle` | Float | Calculé = Σ heures_normales pointages / 8 |
| `project_task_id` | Many2one | Synchronisation avec `project.task` |
| `dependance_ids` | Many2many | Tâches antécédentes (dépendances) |

---

### 2.4. `btp.ressource` — Ressources Humaines Chantier

Gestion des ouvriers et techniciens par chantier.

| Champ | Type | Description |
|-------|------|-------------|
| `employee_id` | Many2one | Employé (requis, lien RH) |
| `qualification` | Selection | `manœuvre` / `ouvrier_qualifié` / `chef_équipe` / `chef_chantier` / `conducteur_travaux` / `ingénieur` / `topographe` |
| `specialite` | Selection | `maçonnerie` / `coffrage` / `ferraillage` / `électricité` / `plomberie` / `peinture` / `étanchéité` / `VRD` |
| `type_contrat` | Selection | `CDI` / `CDD` / `journalier` / `tâcheronnat` |
| `taux_journalier` | Float | Salaire journalier en DH |
| `taux_horaire` | Float | Taux horaire DH (défaut: 17.25 = SMIG BTP 2025) |
| `numero_cnss` | Char | Issu de `employee_id.cnss_number` (readonly) |

---

### 2.5. `btp.pointage` — Pointage avec Géolocalisation

Pointage quotidien des ressources avec géolocalisation GPS.

| Champ | Type | Description |
|-------|------|-------------|
| `ressource_id` | Many2one | Ressource (requis) |
| `chantier_id` | Many2one | Chantier (requis) |
| `tache_id` | Many2one | Tâche (optionnel) |
| `date` | Date | Date de pointage (défaut: aujourd'hui) |
| `heure_debut` / `heure_fin` | Float | Format: 8.5 = 8h30 |
| `heures_normales` | Float | Calculé = `min(heure_fin - heure_debut, 8.0)` |
| `heures_sup_25` / `heures_sup_50` / `heures_sup_100` | Float | Heures supp. (+25% / +50% / +100%) |
| `montant_journee` | Monetary | Calculé (SMIG BTP avec majorations) |
| `latitude` / `longitude` | Float | GPS (7 décimales) |
| `photo_presence` | Binary | Photo de présence géolocalisée |
| `valide` | Boolean | Validation du responsable |

**Calcul SMIG BTP Maroc :**
```
heures_normales = min(heure_fin - heure_debut, 8.0)
montant = heures_normales × taux_horaire
         + heures_sup_25 × taux_horaire × 1.25   # Heures sup. normales
         + heures_sup_50 × taux_horaire × 1.50   # Heures de nuit
         + heures_sup_100 × taux_horaire × 2.00  # Jours fériés
```

---

### 2.6. `btp.situation` — Situations de Travaux

Facturation périodique avec détail par lot (similaire décompte CCAG).

| Champ | Type | Description |
|-------|------|-------------|
| `numero` | Char | Référence auto (séquence) |
| `chantier_id` | Many2one | Chantier (requis) |
| `date_debut_periode` / `date_fin_periode` | Date | Période de facturation |
| `state` | Selection | `brouillon` → `validé` → `facturé` → `payé` |
| `taux_tva` | Selection | 20% ou 14% (TVA marocaine) |
| `montant_periode` | Monetary | Calculé = Σ lignes montant_periode |
| `montant_cumule` | Monetary | Calculé = cumul_précédent + montant_periode |
| `montant_retenue_garantie` | Monetary | Calculé = montant_periode × taux_retenue |
| `montant_tva` | Monetary | Calculé = (montant_periode - retenue) × taux_tva |
| `montant_net` | Monetary | Calculé = montant_ht + TVA |
| `taux_avancement` | Float (%) | Calculé = montant_cumule / montant_total × 100 |
| `move_id` | Many2one | Facture comptable liée (`account.move`) |

**Boutons :**
- `action_valider()` → state = validé
- `action_generer_facture()` → Crée account.move + state = facturé

---

### 2.7. `btp.engin` — Engins de Chantier

| Champ | Type | Description |
|-------|------|-------------|
| `type_engin` | Selection | `pelle` / `chargeuse` / `grue` / `camion` / `compacteur` / `bétonnière` / `groupe_électrogène` / `pompe` |
| `state` | Selection | `disponible` / `en_service` / `en_panne` / `en_maintenance` |
| `immatriculation` | Char | Numéro d'immatriculation (unique) |
| `consommation_gasoil_heure` | Float | Consommation L/h |
| `cout_heure` | Float | Coût horaire en DH |
| `assurance_date_fin` / `visite_technique_date_fin` | Date | Dates d'expiration |
| `alerte_assurance` / `alerte_visite` | Boolean | Calculé = date_fin ≤ aujourd'hui + 30 jours |

---

### 2.8. `btp.approvisionnement` — Approvisionnements

Gestion des besoins en matériaux avec vérification stock.

| Champ | Type | Description |
|-------|------|-------------|
| `product_id` | Many2one | Article (requis) |
| `quantite_demandee` / `quantite_livree` | Float | Quantités |
| `state` | Selection | `demande` / `commandé` / `partiel` / `livré` |
| `urgence` | Boolean | Marquer urgent |
| `purchase_order_id` | Many2one | Bon de commande créé automatiquement |
| `availability_status` | Selection | `en_stock` / `prévisionnel` / `à_commander` (calculé) |
| `shortage_qty` | Float | Calculé = quantité manquante |

**Action :** `action_creer_commande()` → Crée `purchase.order` auprès du fournisseur préféré du produit.

---

### 2.9. `btp.reception` — Réceptions Provisoire / Définitive

| Champ | Type | Description |
|-------|------|-------------|
| `type` | Selection | `provisoire` / `définitive` |
| `date` | Date | Date de réception |
| `pv_file` | Binary | PV signé (PDF) |
| `delai_garantie` | Integer | Délai de garantie en mois (défaut: 12) |
| `date_fin_garantie` | Date | Calculé = date + delai_garantie mois |
| `reserve_ids` | One2many | Liste des réserves |

---

### 2.10. `btp.sous.traitant` — Sous-traitants BTP Maroc

Contrôle de conformité des sous-traitants avec vérification documents légaux.

| Champ | Type | Description |
|-------|------|-------------|
| `numero_rc` | Char | Registre du Commerce |
| `numero_patente` | Char | Patente |
| `numero_if` | Char | Identifiant Fiscal |
| `numero_ice` | Char | Identifiant Commun de l'Entreprise |
| `numero_cnss` | Char | Numéro CNSS |
| `attestation_fiscale_valide` | Date | Date validité attestation |
| `assurance_rc_valide` | Date | Date validité RC |
| `state` | Selection | `actif` / `suspendu` / `résilié` |
| `documents_conformes` | Boolean | Calculé = tous documents valides |

---

### 2.11. `btp.document` — Documents Légaux Chantier

Documents obligatoires au Maroc pour les chantiers BTP.

**Types de documents :** Permis de construire, Autorisation des travaux, Plan béton armé, Plan architecte, Ordre de service, Attestation assurance, PV de réunion, PV de réception, Registre de chantier, Plan HSE, Déclaration d'ouverture, Attestation CNSS, Attestation fiscale, Caution bancaire.

---

## 3. Wizards

### 3.1. `btp.situation.wizard` — Génération de Situations

| Champ | Description |
|-------|-------------|
| `chantier_id` | Chantier (défaut: enregistrement actif) |
| `date_debut` / `date_fin` | Période (requis) |
| `taux_tva` | TVA: 20% ou 14% |
| `reprendre_cumuls` | Reprendre quantités cumulées (défaut: Oui) |

**Action :** `action_generer()` — Crée une situation avec lignes depuis les lots, en reprenant les cumuls de la dernière situation validée.

### 3.2. `btp.cnss.wizard` — Export CNSS DUE

Génère un fichier texte au **format CNSS Maroc** (positions fixes) :
```
E{code_employeur}{mois}{annee}
S{cnss}{cin}{nom}{jours}{salaire_centimes}...
T{nb_employes}{total_jours}{total_salaire_centimes}
```

### 3.3. `btp.cloture.wizard` — Clôture de Chantier

Vérifie les conditions avant clôture : toutes réceptions effectuées, réserves levées, factures payées.

---

## 4. API REST (Pointage Mobile)

| Route | Méthode | Description |
|-------|---------|-------------|
| `/api/btp/pointage` | POST | Pointage mobile avec géolocalisation GPS |
| `/api/btp/chantier/<id>/dashboard` | GET | KPI du chantier (avancement, coûts, ressources) |

---

## 5. Rapports PDF

| Rapport | Description |
|---------|-------------|
| Situation de travaux | Format standard Maroc avec décompte |
| Décompte quantitatif | Avancement par lot |
| PV de Réception | Provisoire/Définitive |
| Registre du personnel | Obligatoire Inspection du Travail |
| Fiche pointage hebdomadaire | Détail heures par ressource |
| Bordereau CNSS | Format DUE |

---

## 6. Sécurité

### Groupes

| Groupe | Droits |
|--------|--------|
| `group_btp_directeur` | CRUD complet sur tous les modèles BTP |
| `group_btp_chef_chantier` | Lecture + Écriture + Création (pas de suppression) |
| `group_btp_compagnon` | Lecture seule |

### Modèles sécurisés

`btp.chantier`, `btp.lot`, `btp.tache`, `btp.ressource`, `btp.pointage`, `btp.engin`, `btp.engin.pointage`, `btp.approvisionnement`, `btp.situation`, `btp.situation.line`, `btp.reception`, `btp.reserve`, `btp.document`, `btp.sous.traitant`, `btp.meteo`, `btp.reunion`, `btp.decision`

---

## 7. Menus & Actions

| Menu | Action |
|------|--------|
| BTP → Chantiers | Liste des chantiers (trée/kanban/liste) |
| BTP → Lots & Tâches | Gestion des lots et tâches |
| BTP → Ressources → Ressources | Ressources humaines |
| BTP → Ressources → Pointages | Saisie et validation des pointages |
| BTP → Ressources → Engins | Parc d'engins |
| BTP → Situations | Situations de travaux à facturer |
| BTP → Approvisionnements | Besoins en matériaux |
| BTP → Sous-traitants | Annuaire sous-traitants |
| BTP → Réunions | PV de réunions de chantier |
| BTP → Rapports | Rapports BTP |
| BTP → Configuration | Paramètres BTP |

---

## 8. Dépendances inter-modules

| Module | Intégration |
|--------|-------------|
| `account` | Génération factures depuis situations de travaux |
| `purchase` | Bon de commande depuis approvisionnement |
| `stock` | Vérification disponibilité matériaux |
| `hr` | Ressources humaines (ouvriers) |
| `project` | Synchronisation tâches ↔ project.task |
| `custom_documents` | GED liée aux chantiers |
| `custom_ai` | Assistant IA sur formulaire chantier |
