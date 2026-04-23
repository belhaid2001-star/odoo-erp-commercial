# Module 8 : Assistant IA — Mohasib (custom_ai)

**Version** : 17.0.2.0.0  
**Catégorie** : Tools  
**Auteur** : ERP Commercial  
**Spécialisation** : Expert-comptable IA BTP Maroc (PCM, TVA 20%, IS, IR)  
**Dépendances** : `base`, `mail`, `sale_management`, `purchase`, `stock`, `account`, `hr`, `crm`, `custom_btp`  

---

## 1. Vue d'ensemble

Module d'intelligence artificielle intégré à l'ERP, spécialisé en **comptabilité BTP Maroc**. Il fournit des conseils, analyses et suggestions contextuelles directement dans chaque module de l'ERP.

**Fournisseurs IA supportés :**
| Fournisseur | Description |
|-------------|-------------|
| **Builtin** | Intelligence intégrée sans API externe (fonctionnement hors-ligne) |
| **OpenAI** | ChatGPT via clé API (modèle configurable : gpt-3.5-turbo, gpt-4...) |
| **Ollama** | Modèle IA local (Llama2, Mistral, etc.) |

---

## 2. Modèles Python

### 2.1. Configuration IA (`res.config.settings` hérité)

Paramètres système de l'IA (admin uniquement) :

| Paramètre | Clé IR | Défaut | Description |
|-----------|--------|--------|-------------|
| `ai_provider` | `custom_ai.provider` | `builtin` | Fournisseur IA |
| `ai_api_key` | `custom_ai.api_key` | — | Clé API OpenAI |
| `ai_api_url` | `custom_ai.api_url` | `https://api.openai.com/v1` | URL de l'API |
| `ai_model` | `custom_ai.model` | `gpt-3.5-turbo` | Modèle IA |
| `ai_temperature` | `custom_ai.temperature` | `0.7` | Créativité (0-2) |

---

### 2.2. `ai.mixin` — Mixin IA (AbstractModel)

Ajoute les capacités IA à n'importe quel modèle via héritage.

**Méthodes publiques :**

```python
ai_generate(prompt, context_data={}, module='general')
    → dict {'success': bool, 'result': str, 'provider': str}

ai_analyze(data, analysis_type='general', module='general')
    → dict with analysis results

ai_suggest(record_data, suggestion_type='general', module='general')
    → dict with suggestions
```

---

### 2.3. `ai.actions` — Actions IA sur Modèles

Injecte la méthode `action_open_ai_wizard()` sur ces modèles :

| Modèle | Label bouton |
|--------|-------------|
| `sale.order` | 🤖 Assistant IA |
| `crm.lead` | 🤖 Assistant IA |
| `purchase.order` | 🤖 Assistant IA |
| `account.move` | 🤖 Assistant IA |
| `stock.picking` | 🤖 Assistant IA |
| `hr.employee` | 🤖 Assistant IA |
| `res.partner` | 🤖 Assistant IA |
| `btp.chantier` | 🏗️ Mohasib |
| `btp.situation` | 🏗️ Mohasib |
| `btp.approvisionnement` | 🏗️ Mohasib |

---

### 2.4. `ai.wizard` — Wizard IA Principal

Interface de dialogue avec l'assistant IA.

#### Champs

| Champ | Type | Description |
|-------|------|-------------|
| `action_type` | Selection | `btp_conseil` / `btp_entry` / `custom` / `accounting_advice` / `accounting_entry` |
| `custom_prompt` | Text | Prompt libre (visible si action_type = custom) |
| `module_name` | Char | Module source (readonly, passé en contexte) |
| `res_model` / `res_id` | Char/Int | Enregistrement source (readonly) |
| `ai_result` | Html | Résultat généré par l'IA |
| `activity_count` | Integer | Nb activités créées (mode vocal) |
| `ai_provider` | Char | Fournisseur utilisé (affiché en résultat) |
| `use_voice_mode` | Boolean | Mode commande vocale |
| `voice_transcript` | Text | Texte transcrit (mode vocal) |

#### Boutons

| Bouton | Méthode | Description |
|--------|---------|-------------|
| 🚀 Analyser | `action_generate()` | Lance la génération IA (mode standard) |
| 📌 Créer activités | `action_generate()` | Crée des activités Odoo (mode vocal) |
| ✅ Appliquer | `action_apply()` | Applique le résultat sur l'enregistrement source |
| Fermer | `special="cancel"` | Ferme le wizard |

---

## 3. Vues

### Vue Wizard (`ai_wizard_form`)

**Mode Standard :**
- Sélection du type d'action (radio)
- Zone de prompt personnalisé
- Informations contextuelles (module, enregistrement source)
- Zone de résultat HTML avec formatage

**Mode Vocal :**
- Transcription vocale
- Création automatique d'activités Odoo

---

## 4. Menus

| Menu | Accès | Action |
|------|-------|--------|
| Assistant IA (racine) | Tous | — |
| Assistant IA | Tous | Ouvre wizard IA en mode global |
| Configuration | Admin uniquement | Paramètres système IA |

---

## 5. Sécurité

**Accès :** `ai.wizard` est accessible à **tous les utilisateurs** (CRUD public).  
**Configuration :** Menu Configuration protégé par `base.group_system` (administrateurs uniquement).

---

## 6. Intégration

L'assistant IA est intégré via des boutons dans les formulaires de :
- Chantiers BTP (analyse avancement, risques, révision prix)
- Factures (analyse fiscal, conseils TVA, IS, IR)
- Opportunités CRM (stratégie commerciale)
- Commandes vente/achat (analyse rentabilité)
- Employés RH (analyse performance)
- Contacts (qualification prospect)
