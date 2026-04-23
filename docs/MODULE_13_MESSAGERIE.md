# Module 13 : Messagerie Avancée (custom_discuss)

**Version** : 17.0.1.0.0  
**Catégorie** : Discuss  
**Auteur** : ERP Commercial  
**Dépendances** : `mail`  

---

## 1. Vue d'ensemble

Extension du système de messagerie Odoo avec modèles de messages réutilisables, priorités de messages et support des notes vocales.

---

## 2. Modèles Python

### 2.1. `mail.template.custom` — Modèles de Messages

Templates personnalisés pour standardiser les communications internes et externes.

| Champ | Type | Options / Description |
|-------|------|----------------------|
| `name` | Char | Nom du modèle (requis) |
| `sequence` | Integer | Ordre d'affichage (défaut: 10) |
| `category` | Selection | `commercial` / `support` / `interne` / `rh` / `comptabilité` / `autre` |
| `subject` | Char | Objet du message |
| `body` | Html | Contenu riche (WYSIWYG) |
| `is_internal` | Boolean | Message interne uniquement (défaut: Non) |
| `active` | Boolean | Actif (défaut: Oui) |
| `company_id` | Many2one | Société |

---

### 2.2. `mail.message` (hérité) — Messages Enrichis

| Champ | Type | Description |
|-------|------|-------------|
| `message_priority` | Selection | `faible` / `normal` (défaut) / `élevé` / `urgent` |
| `is_flagged` | Boolean | Message marqué/étoilé (défaut: Non) |
| `voice_note` | Binary | Enregistrement audio (WebM/Ogg) |
| `voice_note_filename` | Char | Nom du fichier audio |
| `voice_note_duration` | Float | Durée de la note vocale (secondes) |
| `is_voice_message` | Boolean | Est une note vocale (défaut: Non) |

---

## 3. Vues

### Vue Modèle de Message (Formulaire)

- Éditeur HTML pour le contenu du message
- Sélection catégorie et visibilité (interne/externe)
- Prévisualisation du rendu

---

## 4. Menus

| Menu | Action |
|------|--------|
| Discussion → Modèles de message | Liste/gestion des templates |
| Discussion → Rapports → Fiche modèle email | Rapport PDF template |

---

## 5. Sécurité

Accessible à tous les utilisateurs (`base.group_user`).
