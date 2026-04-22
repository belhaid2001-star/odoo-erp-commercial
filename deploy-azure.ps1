#!/usr/bin/env pwsh
# ============================================================
#  Déploiement Odoo ERP Commercial → Azure VM
#  Usage : .\deploy-azure.ps1
#  Prérequis : Azure CLI connecté (az login)
# ============================================================

param(
    [switch]$NoGitPush   # Utiliser si le code est déjà pushé sur GitHub
)

$RG   = "RG-ODOO-ERP"
$VM   = "vm-odoo-erp"
$REPO = "https://github.com/belhaid2001-star/odoo-erp-commercial.git"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Deploiement Odoo ERP Commercial - Azure" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# --- 1. Git push local si demande ---
if (-not $NoGitPush) {
    Write-Host "`n[1/3] Push du code sur GitHub..." -ForegroundColor Yellow
    git -C $PSScriptRoot add -A
    $msg = "deploy: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    git -C $PSScriptRoot commit -m $msg 2>&1 | Where-Object { $_ -notmatch "nothing to commit" }
    git -C $PSScriptRoot push origin main
    Write-Host "    Code pousse sur GitHub." -ForegroundColor Green
} else {
    Write-Host "`n[1/3] Pas de git push (--NoGitPush)." -ForegroundColor Gray
}

# --- 2. Deploiement sur la VM via az vm run-command ---
Write-Host "`n[2/3] Deploiement sur la VM Azure ($VM)..." -ForegroundColor Yellow

$deployScript = @'
export HOME=/root
set -e
cd /opt/odoo-erp-commercial
git remote set-url origin REPO_PLACEHOLDER
git config --local credential.helper ""
GIT_TERMINAL_PROMPT=0 git -c credential.helper="" fetch origin main
git reset --hard origin/main
echo "Code mis a jour : $(git log --oneline -1)"
cp deploy/odoo.prod.conf config/odoo.conf
docker compose -f deploy/docker-compose.prod.yml up -d --force-recreate --remove-orphans
docker compose -f deploy/docker-compose.prod.yml ps
echo "DEPLOY_SUCCESS"
'@
$deployScript = $deployScript.Replace("REPO_PLACEHOLDER", $REPO)

# Ecrire dans un fichier temp pour eviter les problemes d'echappement
$tmpScript = [System.IO.Path]::GetTempFileName() + ".sh"
$deployScript | Out-File -FilePath $tmpScript -Encoding utf8 -NoNewline

Write-Host "    Envoi du script sur la VM..." -ForegroundColor Gray
$output = az vm run-command invoke `
    -g $RG -n $VM `
    --command-id RunShellScript `
    --scripts "@$tmpScript" `
    --query "value[0].message" -o tsv 2>&1

Remove-Item $tmpScript -ErrorAction SilentlyContinue

# --- 3. Affichage du resultat ---
Write-Host "`n[3/3] Resultat :" -ForegroundColor Yellow
Write-Host $output

if ($output -match "DEPLOY_SUCCESS") {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host " Deploiement REUSSI !" -ForegroundColor Green
    Write-Host " URL : https://erp-btp-maroc.swedencentral.cloudapp.azure.com" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "ATTENTION : Verifiez les logs ci-dessus." -ForegroundColor Red
    exit 1
}
