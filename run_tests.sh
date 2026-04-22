#!/bin/bash
# ===========================================================================
#  Script d'exécution des tests — ERP Commercial (Odoo 17)
#  Usage :
#    ./run_tests.sh                    # Tous les tests Odoo
#    ./run_tests.sh sale               # Un seul module
#    ./run_tests.sh sale purchase      # Plusieurs modules
#    ./run_tests.sh --playwright       # Tests E2E Playwright
#    ./run_tests.sh --all              # Tous les tests (Odoo + Playwright)
# ===========================================================================

set -e

# ─── Configuration ───────────────────────────────────────────────────
CONTAINER_NAME="odoo_erp_app"
DB_NAME="odoo_erp_commercial"
DB_HOST="db"
DB_USER="odoo"
DB_PASSWORD="odoo_secret_2026"
ADDONS_PATH="/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons"
LOG_LEVEL="test"

ALL_MODULES=(
    "custom_sale"
    "custom_purchase"
    "custom_stock"
    "custom_accounting"
    "custom_hr"
    "custom_crm"
    "custom_calendar"
    "custom_documents"
    "custom_discuss"
    "custom_contacts"
    "custom_dashboard"
    "custom_ai"
    "custom_btp"
)

# ─── Couleurs ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ─── Fonctions ───────────────────────────────────────────────────────
print_header() {
    echo ""
    echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  ERP Commercial — Exécution des tests${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
    echo ""
}

check_container() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${RED}[ERREUR] Le conteneur '${CONTAINER_NAME}' n'est pas en cours d'exécution.${NC}"
        echo -e "${YELLOW}Lancez : docker compose up -d${NC}"
        exit 1
    fi
}

run_odoo_tests() {
    local module=$1
    echo -e "${YELLOW}[TEST] Exécution des tests pour : ${module}${NC}"

    docker exec "$CONTAINER_NAME" odoo \
        -d "$DB_NAME" \
        --db_host="$DB_HOST" \
        --db_user="$DB_USER" \
        --db_password="$DB_PASSWORD" \
        --addons-path="$ADDONS_PATH" \
        --test-enable \
        --test-tags="/${module}" \
        --stop-after-init \
        --log-level="$LOG_LEVEL" \
        2>&1

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[OK] ${module} — Tests réussis${NC}"
        return 0
    else
        echo -e "${RED}[ÉCHEC] ${module} — Tests échoués${NC}"
        return 1
    fi
}

run_playwright_tests() {
    echo -e "${YELLOW}[TEST] Exécution des tests Playwright E2E${NC}"
    echo ""

    # Vérifier que Playwright est installé
    if ! command -v playwright &> /dev/null; then
        echo -e "${YELLOW}Installation de Playwright...${NC}"
        pip install pytest pytest-playwright playwright
        playwright install chromium --with-deps
    fi

    cd "$(dirname "$0")/custom_addons"
    pytest tests/playwright/ -v \
        --tb=short \
        --screenshot=on \
        --output=test-results/

    local result=$?
    cd ..

    if [ $result -eq 0 ]; then
        echo -e "${GREEN}[OK] Tests Playwright — Tous réussis${NC}"
    else
        echo -e "${RED}[ÉCHEC] Tests Playwright — Certains tests échoués${NC}"
    fi
    return $result
}

show_usage() {
    echo "Usage : $0 [options] [modules...]"
    echo ""
    echo "Options :"
    echo "  --all          Exécuter tous les tests (Odoo + Playwright)"
    echo "  --playwright   Exécuter uniquement les tests Playwright E2E"
    echo "  --install      Installer/réinstaller tous les modules avant les tests"
    echo "  --help         Afficher cette aide"
    echo ""
    echo "Modules disponibles :"
    for mod in "${ALL_MODULES[@]}"; do
        echo "  - ${mod#custom_}"
    done
    echo ""
    echo "Exemples :"
    echo "  $0                     # Tous les tests Odoo"
    echo "  $0 sale purchase       # Tests sale + purchase"
    echo "  $0 --playwright        # Tests E2E uniquement"
    echo "  $0 --all               # Tout exécuter"
}

install_modules() {
    local modules_csv
    modules_csv=$(IFS=,; echo "${ALL_MODULES[*]}")
    echo -e "${YELLOW}[INSTALL] Installation des modules : ${modules_csv}${NC}"
    docker exec "$CONTAINER_NAME" odoo \
        -d "$DB_NAME" \
        --db_host="$DB_HOST" \
        --db_user="$DB_USER" \
        --db_password="$DB_PASSWORD" \
        --addons-path="$ADDONS_PATH" \
        -i "$modules_csv" \
        --stop-after-init \
        --without-demo=False
    echo -e "${GREEN}[OK] Modules installés${NC}"
}

# ─── Main ────────────────────────────────────────────────────────────
print_header

RUN_PLAYWRIGHT=false
RUN_ODOO=true
INSTALL=false
MODULES=()

for arg in "$@"; do
    case "$arg" in
        --all)
            RUN_PLAYWRIGHT=true
            RUN_ODOO=true
            ;;
        --playwright)
            RUN_PLAYWRIGHT=true
            RUN_ODOO=false
            ;;
        --install)
            INSTALL=true
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            MODULES+=("custom_${arg}")
            ;;
    esac
done

# Default : tous les modules Odoo
if [ ${#MODULES[@]} -eq 0 ]; then
    MODULES=("${ALL_MODULES[@]}")
fi

# Vérifier le conteneur Docker
check_container

# Installer si demandé
if [ "$INSTALL" = true ]; then
    install_modules
fi

# Compteurs
PASSED=0
FAILED=0
ERRORS=()

# Exécuter les tests Odoo
if [ "$RUN_ODOO" = true ]; then
    echo -e "${BLUE}── Tests unitaires Odoo ──────────────────────────────────${NC}"
    for module in "${MODULES[@]}"; do
        if run_odoo_tests "$module"; then
            ((PASSED++))
        else
            ((FAILED++))
            ERRORS+=("$module")
        fi
        echo ""
    done
fi

# Exécuter les tests Playwright
if [ "$RUN_PLAYWRIGHT" = true ]; then
    echo -e "${BLUE}── Tests E2E Playwright ─────────────────────────────────${NC}"
    if run_playwright_tests; then
        ((PASSED++))
    else
        ((FAILED++))
        ERRORS+=("playwright-e2e")
    fi
fi

# ─── Résumé ──────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  RÉSUMÉ DES TESTS${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo -e "  Réussis  : ${GREEN}${PASSED}${NC}"
echo -e "  Échoués  : ${RED}${FAILED}${NC}"

if [ ${#ERRORS[@]} -gt 0 ]; then
    echo -e "  Modules en échec : ${RED}${ERRORS[*]}${NC}"
fi

echo ""

if [ "$FAILED" -gt 0 ]; then
    echo -e "${RED}❌ Certains tests ont échoué.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Tous les tests sont passés !${NC}"
    exit 0
fi
