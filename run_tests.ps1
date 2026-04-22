<# ===========================================================================
   Script d'execution des tests — ERP Commercial (Odoo 17) — Windows
   Usage :
     .\run_tests.ps1                      # Tous les tests Odoo
     .\run_tests.ps1 -Modules sale        # Un seul module
     .\run_tests.ps1 -Modules sale,purchase  # Plusieurs modules
     .\run_tests.ps1 -Playwright          # Tests E2E Playwright
     .\run_tests.ps1 -All                 # Tous les tests (Odoo + Playwright)
     .\run_tests.ps1 -Install             # Installer les modules d'abord
=========================================================================== #>

param(
    [string[]]$Modules = @(),
    [switch]$Playwright,
    [switch]$All,
    [switch]$Install,
    [switch]$Help
)

# --- Configuration ---
$ContainerName = "odoo_erp_app"
$DbName        = "odoo_erp_commercial"
$DbHost        = "db"
$DbUser        = "odoo"
$DbPassword    = "odoo_secret_2026"
$AddonsPath    = "/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons"
$LogLevel      = "test"

$AllModules = @(
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

# --- Aide ---
if ($Help) {
    Write-Host @"

  ERP Commercial — Script de Tests
  =================================

  Usage :
    .\run_tests.ps1                          # Tous les tests Odoo
    .\run_tests.ps1 -Modules sale            # Un seul module
    .\run_tests.ps1 -Modules sale,purchase   # Plusieurs modules
    .\run_tests.ps1 -Playwright              # Tests E2E Playwright uniquement
    .\run_tests.ps1 -All                     # Tous les tests
    .\run_tests.ps1 -Install                 # Installer les modules avant les tests

  Modules disponibles :
    sale, purchase, stock, accounting, hr, crm,
    calendar, documents, discuss, contacts, dashboard, ai, btp

"@
    exit 0
}

# --- Fonctions ---
function Write-Header {
    Write-Host ""
    Write-Host "==============================================================" -ForegroundColor Cyan
    Write-Host "  ERP Commercial — Execution des tests" -ForegroundColor Cyan
    Write-Host "==============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-Container {
    $running = docker ps --format '{{.Names}}' | Where-Object { $_ -eq $ContainerName }
    if (-not $running) {
        Write-Host "[ERREUR] Le conteneur '$ContainerName' n'est pas en cours d'execution." -ForegroundColor Red
        Write-Host "Lancez : docker compose up -d" -ForegroundColor Yellow
        exit 1
    }
}

function Install-Modules {
    $modulesCsv = $AllModules -join ","
    Write-Host "[INSTALL] Installation des modules : $modulesCsv" -ForegroundColor Yellow

    docker exec $ContainerName odoo `
        -d $DbName `
        --db_host=$DbHost `
        --db_user=$DbUser `
        --db_password=$DbPassword `
        --addons-path=$AddonsPath `
        -i $modulesCsv `
        --stop-after-init `
        --without-demo=False

    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Modules installes" -ForegroundColor Green
    } else {
        Write-Host "[ERREUR] Echec d'installation" -ForegroundColor Red
        exit 1
    }
}

function Invoke-OdooTests {
    param([string]$Module)

    Write-Host "[TEST] Execution des tests pour : $Module" -ForegroundColor Yellow

    docker exec $ContainerName odoo `
        -d $DbName `
        --db_host=$DbHost `
        --db_user=$DbUser `
        --db_password=$DbPassword `
        --addons-path=$AddonsPath `
        --test-enable `
        --test-tags="/$Module" `
        --stop-after-init `
        --log-level=$LogLevel

    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] $Module — Tests reussis" -ForegroundColor Green
        return $true
    } else {
        Write-Host "[ECHEC] $Module — Tests echoues" -ForegroundColor Red
        return $false
    }
}

function Invoke-PlaywrightTests {
    Write-Host "[TEST] Execution des tests Playwright E2E" -ForegroundColor Yellow
    Write-Host ""

    # Verifier que Playwright est installe
    $pwInstalled = pip show playwright 2>$null
    if (-not $pwInstalled) {
        Write-Host "Installation de Playwright..." -ForegroundColor Yellow
        pip install pytest pytest-playwright playwright
        playwright install chromium --with-deps
    }

    Push-Location "$PSScriptRoot\custom_addons"
    pytest tests/playwright/ -v --tb=short --screenshot=on --output=test-results/
    $result = $LASTEXITCODE
    Pop-Location

    if ($result -eq 0) {
        Write-Host "[OK] Tests Playwright — Tous reussis" -ForegroundColor Green
        return $true
    } else {
        Write-Host "[ECHEC] Tests Playwright — Certains tests echoues" -ForegroundColor Red
        return $false
    }
}

# --- Main ---
Write-Header
Test-Container

$RunOdoo       = -not $Playwright
$RunPlaywright = $Playwright -or $All

if ($All) { $RunOdoo = $true }

# Determiner les modules a tester
if ($Modules.Count -eq 0) {
    $TestModules = $AllModules
} else {
    $TestModules = $Modules | ForEach-Object { "custom_$_" }
}

# Installer si demande
if ($Install) {
    Install-Modules
}

# Compteurs
$Passed = 0
$Failed = 0
$Errors = @()

# Tests Odoo
if ($RunOdoo) {
    Write-Host "-- Tests unitaires Odoo -----------------------------------------------" -ForegroundColor Cyan
    foreach ($mod in $TestModules) {
        $success = Invoke-OdooTests -Module $mod
        if ($success) {
            $Passed++
        } else {
            $Failed++
            $Errors += $mod
        }
        Write-Host ""
    }
}

# Tests Playwright
if ($RunPlaywright) {
    Write-Host "-- Tests E2E Playwright -----------------------------------------------" -ForegroundColor Cyan
    $success = Invoke-PlaywrightTests
    if ($success) {
        $Passed++
    } else {
        $Failed++
        $Errors += "playwright-e2e"
    }
}

# --- Resume ---
Write-Host ""
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "  RESUME DES TESTS" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "  Reussis  : $Passed" -ForegroundColor Green
Write-Host "  Echoues  : $Failed" -ForegroundColor $(if ($Failed -gt 0) { "Red" } else { "Green" })

if ($Errors.Count -gt 0) {
    Write-Host "  Modules en echec : $($Errors -join ', ')" -ForegroundColor Red
}

Write-Host ""

if ($Failed -gt 0) {
    Write-Host "Certains tests ont echoue." -ForegroundColor Red
    exit 1
} else {
    Write-Host "Tous les tests sont passes !" -ForegroundColor Green
    exit 0
}
