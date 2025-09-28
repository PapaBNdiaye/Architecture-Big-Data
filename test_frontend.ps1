# Script de test pour le frontend
# Vérifie que l'interface se charge correctement

$FRONTEND_URL = "http://localhost:5173"
$tests_passed = 0
$total_tests = 2

Write-Host "Demarrage des tests du frontend" -ForegroundColor Cyan
Write-Host ("=" * 40) -ForegroundColor Yellow

# Test 1: Page d'accueil accessible
Write-Host "Test de l'acces a la page d'accueil..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "$FRONTEND_URL" -Method GET
    if ($response.StatusCode -eq 200) {
        Write-Host "Page d'accueil accessible" -ForegroundColor Green
        $tests_passed++
    } else {
        Write-Host "Code HTTP inattendu: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "Erreur acces page d'accueil: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Contenu HTML valide
Write-Host "Test du contenu HTML..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "$FRONTEND_URL" -Method GET
    $content = $response.Content

    # Vérifier la présence d'éléments clés
    $checks = @(
        @{ Name = "Titre de la page"; Pattern = "Architecture Lambda" },
        @{ Name = "Titre des filtres"; Pattern = "Configuration des filtres" },
        @{ Name = "Titre des analyses"; Pattern = "Analyses meteorologiques" }
    )

    $content_valid = $true
    foreach ($check in $checks) {
        if ($content -match $check.Pattern) {
            Write-Host "  - $($check.Name): Present" -ForegroundColor Green
        } else {
            Write-Host "  - $($check.Name): Manquant" -ForegroundColor Red
            $content_valid = $false
        }
    }

    if ($content_valid) {
        Write-Host "Contenu HTML valide" -ForegroundColor Green
        $tests_passed++
    } else {
        Write-Host "Contenu HTML incomplet" -ForegroundColor Red
    }
} catch {
    Write-Host "Erreur verification contenu: $($_.Exception.Message)" -ForegroundColor Red
}

# Résumé des tests
Write-Host ("=" * 40) -ForegroundColor Yellow
Write-Host "Resultats frontend: $tests_passed/$total_tests tests reussis" -ForegroundColor Cyan

if ($tests_passed -eq $total_tests) {
    Write-Host "Frontend OK !" -ForegroundColor Green
} else {
    Write-Host "Problemes avec le frontend" -ForegroundColor Yellow
}