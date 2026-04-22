#!/bin/bash
# =============================================================================
# Script de migration vers données marocaines
# Base de données : odoo_erp_commercial
# À exécuter en tant que : psql -U odoo -d odoo_erp_commercial
# =============================================================================

set -e
DB="odoo_erp_commercial"
PSQL="docker exec -i odoo-db psql -U odoo -d $DB"

echo "=== Migration vers données marocaines ==="

# ─────────────────────────────────────────────────────────────────────────────
# 1. Entreprise principale → Belhaid Construction SARL
# ─────────────────────────────────────────────────────────────────────────────
$PSQL <<'SQL'
UPDATE res_company
SET
    name      = 'Belhaid Construction SARL',
    street    = 'Bd Zerktouni, Imm. Al Fath',
    street2   = 'Bureau 5, 3ème étage',
    city      = 'Casablanca',
    zip       = '20000',
    phone     = '+212 5 22 00 00 01',
    email     = 'contact@belhaid-construction.ma',
    website   = 'https://www.belhaid-construction.ma',
    vat       = 'MA-RC-12345'
WHERE id = 1;
SQL
echo "✓ Entreprise mise à jour"

# Mettre à jour le partenaire lié à l'entreprise
$PSQL <<'SQL'
UPDATE res_partner
SET
    name    = 'Belhaid Construction SARL',
    street  = 'Bd Zerktouni, Imm. Al Fath',
    city    = 'Casablanca',
    zip     = '20000',
    phone   = '+212 5 22 00 00 01',
    email   = 'contact@belhaid-construction.ma',
    website = 'https://www.belhaid-construction.ma'
WHERE id = (SELECT partner_id FROM res_company WHERE id = 1);
SQL
echo "✓ Partenaire entreprise mis à jour"

# ─────────────────────────────────────────────────────────────────────────────
# 2. Devise : MAD
# ─────────────────────────────────────────────────────────────────────────────
$PSQL <<'SQL'
-- Activer MAD
UPDATE res_currency SET active = true WHERE name = 'MAD';
-- Désactiver USD et EUR si non utilisé
-- UPDATE res_currency SET active = false WHERE name IN ('USD') AND name NOT IN (
--     SELECT currency_id::text FROM account_move WHERE state='posted' LIMIT 1
-- );
-- Mettre MAD comme devise principale de la société
UPDATE res_company
SET currency_id = (SELECT id FROM res_currency WHERE name = 'MAD' LIMIT 1)
WHERE id = 1;
SQL
echo "✓ Devise MAD configurée"

# ─────────────────────────────────────────────────────────────────────────────
# 3. Pays et ville par défaut → Maroc
# ─────────────────────────────────────────────────────────────────────────────
$PSQL <<'SQL'
UPDATE res_company
SET country_id = (SELECT id FROM res_country WHERE code = 'MA' LIMIT 1),
    state_id   = NULL
WHERE id = 1;

UPDATE res_partner
SET   country_id = (SELECT id FROM res_country WHERE code = 'MA' LIMIT 1),
      state_id   = NULL
WHERE id = (SELECT partner_id FROM res_company WHERE id = 1);
SQL
echo "✓ Pays → Maroc"

# ─────────────────────────────────────────────────────────────────────────────
# 4. Supprimer / réinitialiser les partenaires de démo américains
#    (on garde les contacts qui ont des transactions)
# ─────────────────────────────────────────────────────────────────────────────
$PSQL <<'SQL'
-- Supprimer les partenaires de démo inutilisés (pas de facture, ni commande)
DELETE FROM res_partner
WHERE id NOT IN (
    SELECT DISTINCT partner_id FROM sale_order      WHERE partner_id IS NOT NULL
    UNION
    SELECT DISTINCT partner_id FROM purchase_order  WHERE partner_id IS NOT NULL
    UNION
    SELECT DISTINCT partner_id FROM account_move    WHERE partner_id IS NOT NULL
    UNION
    SELECT partner_id FROM res_company              WHERE partner_id IS NOT NULL
    UNION
    SELECT DISTINCT partner_id FROM res_users       WHERE partner_id IS NOT NULL
)
AND customer_rank = 0 AND supplier_rank = 0
AND id != 1  -- toujours garder le partenaire de base
AND (
    city IN ('San Francisco','New York','Chicago','Los Angeles','Houston',
             'Portland','Denver','Seattle','Austin','Boston','Miami',
             'Atlanta','Phoenix','San Diego','Dallas')
    OR country_id = (SELECT id FROM res_country WHERE code = 'US' LIMIT 1)
);
SQL
echo "✓ Partenaires démo US supprimés (sans transactions)"

# ─────────────────────────────────────────────────────────────────────────────
# 5. Insérer des partenaires marocains de référence
# ─────────────────────────────────────────────────────────────────────────────
$PSQL <<'SQL'
-- Clients marocains
INSERT INTO res_partner (name, street, city, zip, phone, email, customer_rank, supplier_rank,
                         country_id, company_type, active)
SELECT
    v.name, v.street, v.city, v.zip, v.phone, v.email,
    1, 0,
    (SELECT id FROM res_country WHERE code='MA' LIMIT 1),
    'company', true
FROM (VALUES
    ('Al Omrane Développement',    'Avenue Annakhil, Hay Ryad',          'Rabat',         '10034', '+212 5 37 71 00 00', 'contact@alomrane.ma'),
    ('Addoha Groupe',              'Lot Attaoufik, Route de Rabat',       'Casablanca',    '20100', '+212 5 22 58 00 00', 'info@addoha.ma'),
    ('CIH Bank',                   '187 Avenue Hassan II',                'Casablanca',    '20000', '+212 5 22 47 10 00', 'clientele@cih.co.ma'),
    ('ONCF',                       '8 bis Rue Abderrahman El Ghafiki',    'Rabat',         '10100', '+212 5 37 77 47 47', 'contact@oncf.ma'),
    ('Marjane Holding',            'Angle Route de Meknes & Av. Modibo', 'Rabat',         '10090', '+212 5 37 68 70 00', 'info@marjane.ma'),
    ('SODEA Construction',         '22 Rue Ibnou Khaldoun',               'Fès',           '30000', '+212 5 35 62 30 00', 'sodea@fes.ma'),
    ('Immobilière Ennakhil',       'Route de Marrakech km 12',            'Marrakech',     '40000', '+212 5 24 33 50 00', 'info@ennakhil.ma'),
    ('BTP Tanger SARL',            'Zone Industrielle Mghogha',           'Tanger',        '90000', '+212 5 39 37 20 00', 'contact@btp-tanger.ma'),
    ('Ciments du Maroc',           'Route des Aïn Sbaâ',                  'Casablanca',    '20250', '+212 5 22 67 67 67', 'cmadmin@cimentsdumaroc.com'),
    ('Agences de Crédit du Maroc', 'Km 7 Route El Jadida',                'Casablanca',    '20230', '+212 5 22 99 99 99', 'info@acm.co.ma')
) AS v(name, street, city, zip, phone, email)
WHERE NOT EXISTS (
    SELECT 1 FROM res_partner WHERE name = v.name
);
SQL
echo "✓ Clients marocains insérés"

$PSQL <<'SQL'
-- Fournisseurs marocains
INSERT INTO res_partner (name, street, city, zip, phone, email, customer_rank, supplier_rank,
                         country_id, company_type, active)
SELECT
    v.name, v.street, v.city, v.zip, v.phone, v.email,
    0, 1,
    (SELECT id FROM res_country WHERE code='MA' LIMIT 1),
    'company', true
FROM (VALUES
    ('BMCE Matériaux',              'Zone Industrielle Sidi Bernoussi',    'Casablanca', '20600', '+212 5 22 76 76 76', 'bmce-mat@gmail.com'),
    ('Holcim Maroc',                'Route de Rabat, BP 38',               'Settat',     '26000', '+212 5 23 72 50 00', 'info@holcim.ma'),
    ('Métalsa',                     '5 Rue Jean Jaurès',                   'Casablanca', '20100', '+212 5 22 30 31 00', 'metalsa@casanet.ma'),
    ('Entreprise Hadj Benali',      'Quartier Industriel',                 'Fès',        '30050', '+212 5 35 64 10 00', 'hadj-benali@fes.ma'),
    ('Electricité Générale Maroc',  'Bd Mohammed V',                       'Rabat',      '10000', '+212 5 37 20 50 00', 'egm@rabat.ma'),
    ('Plomberie & Sanitaire Lahcen','Hay Mohammadi, Rue 7',                'Salé',       '11000', '+212 5 37 88 10 00', 'lahcen-plomberie@sal.ma')
) AS v(name, street, city, zip, phone, email)
WHERE NOT EXISTS (
    SELECT 1 FROM res_partner WHERE name = v.name
);
SQL
echo "✓ Fournisseurs marocains insérés"

# ─────────────────────────────────────────────────────────────────────────────
# 6. Mettre à jour l'utilisateur admin → Nom marocain
# ─────────────────────────────────────────────────────────────────────────────
$PSQL <<'SQL'
UPDATE res_partner
SET name = 'Belhaid Admin',
    city = 'Casablanca',
    country_id = (SELECT id FROM res_country WHERE code='MA' LIMIT 1)
WHERE id = (
    SELECT partner_id FROM res_users WHERE login = 'admin' LIMIT 1
);
SQL
echo "✓ Utilisateur admin mis à jour"

# ─────────────────────────────────────────────────────────────────────────────
# 7. Paramètres système : langue et localisation marocaine
# ─────────────────────────────────────────────────────────────────────────────
$PSQL <<'SQL'
-- Numérotation fiscale marocaine
INSERT INTO ir_config_parameter (key, value)
VALUES ('l10n_ma.use_pcm', 'True')
ON CONFLICT (key) DO UPDATE SET value = 'True';

-- Timezone Casablanca
UPDATE res_users SET tz = 'Africa/Casablanca' WHERE id > 0;
UPDATE res_company SET partner_tz = 'Africa/Casablanca' WHERE id = 1 AND EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='res_company' AND column_name='partner_tz'
);
SQL
echo "✓ Paramètres localisation marocaine"

# ─────────────────────────────────────────────────────────────────────────────
# DONE
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "============================================"
echo "  Migration données marocaines terminée ✅  "
echo "============================================"
