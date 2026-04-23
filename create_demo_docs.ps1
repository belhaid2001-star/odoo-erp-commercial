# Script de creation des documents demo GED via XML-RPC

$OdooUrl = "https://erp-btp-maroc.swedencentral.cloudapp.azure.com"
$DB = "odoo_erp_commercial"
$UID = 2
$PWD_ODOO = "admin"

# SSL bypass
Add-Type @"
using System.Net;
using System.Security.Cryptography.X509Certificates;
public class TrustAllDemo : ICertificatePolicy {
    public bool CheckValidationResult(ServicePoint s, X509Certificate c, WebRequest r, int e) { return true; }
}
"@ -ErrorAction SilentlyContinue
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllDemo

function Create-OdooDoc($name, $folderId, $docType, $state, $expiry, $notes, $content, $filename) {
    $b64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($content))
    
    $expiryXml = ""
    if ($expiry) {
        $expiryXml = "<member><name>expiration_date</name><value><string>$expiry</string></value></member>"
    }

    $xml = @"
<?xml version="1.0"?>
<methodCall>
  <methodName>execute_kw</methodName>
  <params>
    <param><value><string>$DB</string></value></param>
    <param><value><int>$UID</int></value></param>
    <param><value><string>$PWD_ODOO</string></value></param>
    <param><value><string>document.document</string></value></param>
    <param><value><string>create</string></value></param>
    <param><value><array><data>
      <value><struct>
        <member><name>name</name><value><string>$name</string></value></member>
        <member><name>folder_id</name><value><int>$folderId</int></value></member>
        <member><name>document_type</name><value><string>$docType</string></value></member>
        <member><name>state</name><value><string>$state</string></value></member>
        <member><name>file</name><value><string>$b64</string></value></member>
        <member><name>file_name</name><value><string>$filename</string></value></member>
        <member><name>notes</name><value><string>$notes</string></value></member>
        $expiryXml
      </struct></value>
    </data></array></value></param>
    <param><value><struct></struct></value></param>
  </params>
</methodCall>
"@
    $r = Invoke-WebRequest -Uri "$OdooUrl/xmlrpc/2/object" -Method POST -Body $xml -ContentType "text/xml"
    $id = [regex]::Match($r.Content, '<int>(\d+)</int>').Groups[1].Value
    if ($id) {
        Write-Host "[OK] '$name' cree -> ID=$id"
    } else {
        Write-Host "[ERREUR] '$name' : $($r.Content.Substring(0,300))"
    }
}

Write-Host "=== Creation des documents demo GED ==="

# Dossiers: General=1, Contrats=2, RH=3, Finance=4, Juridique=5

Create-OdooDoc `
    "Contrat sous-traitance - Al Omrane Developpement" `
    2 "contract" "validated" "2026-12-31" `
    "Contrat pour les travaux de gros oeuvre du projet Residence Al Farah a Casablanca. Montant: 2 500 000 MAD HT. Duree: 8 mois." `
    "CONTRAT DE SOUS-TRAITANCE`nParties: Construction SARL / Al Omrane Developpement`nObjet: Travaux gros oeuvre - Residence Al Farah Casablanca`nMontant HT: 2 500 000 MAD`nDuree: 8 mois - Debut: 01/01/2026`nExpiration: 31/12/2026" `
    "contrat_sous_traitance_al_omrane.txt"

Create-OdooDoc `
    "Devis chantier - Immeuble R+5 Hay Riad Rabat" `
    1 "other" "validated" "" `
    "Devis pour lot gros oeuvre et facade. Client: Al Omrane. Montant total: 4 200 000 MAD HT. Validite: 60 jours." `
    "DEVIS CHANTIER`nClient: Al Omrane`nChantier: Immeuble R+5 Hay Riad Rabat`nLot: Gros oeuvre + Facade`nMontant HT: 4 200 000 MAD`nDate: 15/03/2026 - Validite: 60 jours" `
    "devis_chantier_r5_hay_riad.txt"

Create-OdooDoc `
    "Facture Holcim Maroc - Ciment Avril 2026" `
    4 "invoice" "validated" "" `
    "Facture ciment CPJ 45: 200 tonnes x 1 050 MAD/t. Total HT: 210 000 MAD. TVA 20%: 42 000 MAD. Total TTC: 252 000 MAD." `
    "FACTURE FOURNISSEUR - Holcim Maroc`nN: HLM-2026-04-0892`nProduit: Ciment CPJ 45 - 200 tonnes`nPrix unitaire: 1 050 MAD/t`nTotal HT: 210 000 MAD`nTVA 20%: 42 000 MAD`nTotal TTC: 252 000 MAD`nEcheance: 30/05/2026" `
    "facture_holcim_ciment_avril2026.txt"

Create-OdooDoc `
    "Attestation CNSS - Mohamed Alami 2025" `
    3 "certificate" "validated" "2026-12-31" `
    "Attestation cotisations CNSS 2025 pour Mohamed Alami, Matricule EMP-042. Cotisations annuelles: 18 540 MAD." `
    "ATTESTATION CNSS`nEmploye: Mohamed Alami`nMatricule: EMP-042`nPeriode: Janvier - Decembre 2025`nCotisations versees: 18 540 MAD`nDelivree le: 10/01/2026`nValable jusqu au: 31/12/2026" `
    "attestation_cnss_m_alami_2025.txt"

Create-OdooDoc `
    "Registre de Commerce - Construction SARL" `
    5 "certificate" "validated" "2027-06-30" `
    "RC N 12345/Casablanca. Societe: Construction SARL. Capital social: 500 000 MAD. Gerant: Belhaid. Date creation: 01/03/2020." `
    "REGISTRE DE COMMERCE`nSociete: Construction SARL`nRC N: 12345/Casablanca`nCapital social: 500 000 MAD`nGerant: Belhaid`nDate creation: 01/03/2020`nValable jusqu au: 30/06/2027" `
    "registre_commerce_construction_sarl.txt"

Create-OdooDoc `
    "Plan HSE 2026 - Procedures securite chantier" `
    1 "procedure" "validated" "" `
    "Procedures securite chantier: EPI obligatoires, evacuation, premiers secours, inspections hebdomadaires. Formations HSE trimestrielles. Responsable: Karim Benali." `
    "PLAN HSE 2026 - PROCEDURES SECURITE CHANTIER`nEquipements de protection individuelle obligatoires`nProcedures evacuation et premiers secours`nInspections hebdomadaires securite`nFormations HSE: Q1, Q2, Q3, Q4 2026`nResponsable HSE: Karim Benali`nMise a jour: 01/01/2026" `
    "plan_hse_procedures_securite_2026.txt"

Write-Host "=== Termine ==="
