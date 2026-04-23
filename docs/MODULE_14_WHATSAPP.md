# Module 14 : Intégration WhatsApp (custom_whatsapp)

**Version** : 17.0.1.0.0  
**Catégorie** : Communication  
**Auteur** : ERP Commercial  
**Dépendances** : `base`, `contacts`, `mail`, `sale_management`, `account`  

---

## 1. Vue d'ensemble

Module d'envoi de messages WhatsApp depuis l'ERP, avec gestion de templates, historique des envois et intégration dans les fiches contacts, ventes et factures.

**Fonctionnement :** Ouvre **WhatsApp Web** ou **l'application mobile** via le lien universel `wa.me/{numero}?text={message_encodé}`.

---

## 2. Modèles Python

### 2.1. `whatsapp.message` — Messages WhatsApp

Historique de tous les messages envoyés.

| Champ | Type | Description |
|-------|------|-------------|
| `name` | Char | Référence auto (séquence, readonly) |
| `partner_id` | Many2one | Destinataire (requis) |
| `phone` | Char | Numéro WhatsApp (requis) |
| `message` | Text | Contenu du message (requis) |
| `template_id` | Many2one | Template utilisé |
| `model_name` | Char | Modèle source (ex: `sale.order`) |
| `res_id` | Integer | ID de l'enregistrement source |
| `record_name` | Char | Nom de l'enregistrement source |
| `send_date` | Datetime | Date et heure d'envoi |
| `user_id` | Many2one | Envoyé par (défaut: utilisateur courant) |
| `state` | Selection | `brouillon` / `envoyé` / `échoué` |
| `error_message` | Text | Message d'erreur (si échoué) |

#### Méthodes

```python
_format_phone_for_whatsapp(phone)
    Formats acceptés en entrée :
    - 0612345678     →  212612345678
    - 212612345678   →  212612345678
    - +212612345678  →  212612345678
    Retour : numéro sans "+", pour URL wa.me

action_send_whatsapp()
    1. Valide le numéro de téléphone
    2. Génère URL : wa.me/{phone}?text={message_encodé}
    3. state = 'envoyé'
    4. Enregistre dans le chatter du partenaire
    5. Retourne action d'ouverture URL (WhatsApp Web/App)

action_resend()
    Remet en brouillon et relance action_send_whatsapp()
```

---

### 2.2. `whatsapp.template` — Templates de Messages

| Champ | Type | Description |
|-------|------|-------------|
| `name` | Char | Nom du template (requis) |
| `category` | Selection | `général` / `vente` / `facture` / `livraison` / `relance` / `félicitation` / `promotion` |
| `body` | Text | Corps du message avec variables (requis) |
| `model_name` | Selection | Modèle associé : `res.partner` / `sale.order` / `account.move` / `stock.picking` |
| `active` | Boolean | Actif (défaut: Oui) |

#### Variables disponibles dans les templates

| Variable | Valeur injectée |
|----------|-----------------|
| `{partner_name}` | Nom du contact |
| `{company_name}` | Nom de la société |
| `{amount}` | Montant formaté en DH |
| `{reference}` | Numéro du document |
| `{date}` | Date d'aujourd'hui |
| `{salesperson}` | Nom du vendeur assigné |

**Exemple de template :**
```
Bonjour {partner_name},

Votre commande {reference} est confirmée.
Montant : {amount} DH TTC.

Cordialement,
{salesperson}
{company_name}
```

#### Méthode

```python
render_template(record)
    Substitue toutes les variables avec les données de "record"
    Retourne le message prêt à envoyer
```

---

### 2.3. `res.partner` (hérité) — Champs WhatsApp

| Champ | Type | Description |
|-------|------|-------------|
| `whatsapp_number` | Char | Numéro WhatsApp dédié (format +212 recommandé) |
| `whatsapp_opt_in` | Boolean | Autorisé à recevoir des messages (défaut: Oui) |
| `whatsapp_message_ids` | One2many | Historique messages envoyés |
| `whatsapp_message_count` | Integer | Calculé = nb messages envoyés |

#### Méthodes

| Méthode | Description |
|---------|-------------|
| `action_send_whatsapp()` | Ouvre wizard d'envoi avec le contact pré-rempli |
| `action_view_whatsapp_messages()` | Liste tous les messages du contact |

---

### 2.4. `whatsapp.send.wizard` — Wizard d'Envoi

Interface d'envoi depuis n'importe quel module.

| Champ | Type | Description |
|-------|------|-------------|
| `is_mass_send` | Boolean | Mode envoi groupé (défaut: Non) |
| `partner_id` | Many2one | Destinataire unique |
| `phone` | Char | Numéro direct |
| `partner_ids` | Many2many | Destinataires multiples (mode groupé) |
| `template_id` | Many2one | Template WhatsApp |
| `message` | Text | Message final personnalisable |

---

## 3. Vues

### Vue Message (Formulaire)

- Header avec boutons : 📱 Envoyer via WhatsApp | 🔄 Renvoyer
- Barre d'état : brouillon → envoyé / échoué
- Formulaire : Destinataire, téléphone, template, message éditable
- Zone d'erreur si état = échoué

### Vue Template (Formulaire)

- Éditeur de corps de message avec aide sur les variables
- Sélection catégorie et modèle associé

### Smart button sur la fiche Contact

- **💬 Messages WhatsApp** (avec compteur) → liste des messages

---

## 4. Menus

| Menu | Action |
|------|--------|
| **WhatsApp** (racine) | — |
| WhatsApp → ✉️ Nouveau message | Ouvre wizard d'envoi |
| WhatsApp → 📱 Messages | Liste/historique de tous les messages |
| WhatsApp → Configuration → Templates | Gestion des templates |

---

## 5. Sécurité

| Modèle | Utilisateurs | Administrateurs |
|--------|-------------|-----------------|
| `whatsapp.message` | Lecture + Création (pas de suppression) | CRUD complet |
| `whatsapp.template` | Lecture seule | CRUD complet |
| `whatsapp.send.wizard` | CRUD | CRUD |
