# Script de test pour l'API Weather Batch
# Teste les differentes fonctionnalites de l'API

$BASE_URL = "http://localhost:8000"
$tests_passed = 0
$total_tests = 4

Write-Host "Demarrage des tests de l'API Weather Batch" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Yellow

# Test 1: Endpoint racine
Write-Host "Test de l'endpoint racine..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/" -Method GET
    $data = $response.Content | ConvertFrom-Json
    if ($data.message -and $data.version) {
        Write-Host "Endpoint racine OK" -ForegroundColor Green
        $tests_passed++
    } else {
        Write-Host "Reponse invalide" -ForegroundColor Red
    }
} catch {
    Write-Host "Erreur endpoint racine: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Lancement de requete
Write-Host "Test de lancement de requete..." -ForegroundColor Blue
try {
    $payload = @{
        locations = @("Paris,FR")
        startDate = "2024-01-01"
        endDate = "2024-03-31"
        metrics = @("temp")
        agg = "avg_by_month"
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "$BASE_URL/run" -Method POST -ContentType "application/json" -Body $payload
    $data = $response.Content | ConvertFrom-Json

    if ($data.task_id) {
        $task_id = $data.task_id
        Write-Host "Requete lancee avec task_id: $task_id" -ForegroundColor Green
        $tests_passed++
    } else {
        Write-Host "Pas de task_id dans la reponse" -ForegroundColor Red
    }
} catch {
    Write-Host "Erreur lancement requete: $($_.Exception.Message)" -ForegroundColor Red
    $task_id = $null
}

# Test 3: Statut de la tache
if ($task_id) {
    Write-Host "Test du statut de la tache $task_id..." -ForegroundColor Blue
    try {
        $response = Invoke-WebRequest -Uri "$BASE_URL/status/$task_id" -Method GET
        $data = $response.Content | ConvertFrom-Json

        if ($data.state) {
            $state = $data.state
            Write-Host "Statut de la tache: $state" -ForegroundColor Green
            $tests_passed++
        } else {
            Write-Host "Pas de state dans la reponse" -ForegroundColor Red
        }
    } catch {
        Write-Host "Erreur verification statut: $($_.Exception.Message)" -ForegroundColor Red
    }

    # Test 4: Recuperation des resultats
    Write-Host "Test de recuperation des resultats pour $task_id..." -ForegroundColor Blue
    $max_attempts = 10
    $attempt = 0
    $results = $null

    while ($attempt -lt $max_attempts -and -not $results) {
        try {
            $response = Invoke-WebRequest -Uri "$BASE_URL/fetch/$task_id" -Method GET
            $data = $response.Content | ConvertFrom-Json

            if ($data.data) {
                $results = $data.data
                Write-Host "Resultats recuperes: $($results.Count) enregistrements" -ForegroundColor Green
                $tests_passed++
                break
            }
        } catch {
            $error_data = $_.Exception.Response
            if ($error_data.StatusCode -eq 400) {
                $attempt++
                Write-Host "Tache pas encore terminee, tentative $attempt/$max_attempts" -ForegroundColor Yellow
                Start-Sleep -Seconds 3
            } else {
                Write-Host "Erreur recuperation resultats: $($_.Exception.Message)" -ForegroundColor Red
                break
            }
        }
    }

    if (-not $results) {
        Write-Host "Timeout: tache pas terminee dans le temps imparti" -ForegroundColor Red
    }

    # Validation des resultats
    if ($results) {
        Write-Host "Validation des resultats..." -ForegroundColor Blue
        try {
            $valid = $true

            if (-not ($results -is [array]) -or $results.Count -eq 0) {
                $valid = $false
            }

            if ($valid) {
                $sample = $results[0]
                $required_fields = @("metric_date", "location", "metric_name", "metric_value", "source")

                foreach ($field in $required_fields) {
                    if (-not $sample.PSObject.Properties.Name.Contains($field)) {
                        $valid = $false
                        break
                    }
                }

                if ($valid) {
                    # Verifier les types et valeurs
                    if ($sample.source -ne "visualcrossing") { $valid = $false }
                    if ($sample.metric_name -notin @("avg_temp_c", "sum_precip_mm", "avg_humidity", "avg_windspeed")) { $valid = $false }
                }
            }

            if ($valid) {
                Write-Host "Structure des resultats valide" -ForegroundColor Green
            } else {
                Write-Host "Structure des resultats invalide" -ForegroundColor Red
            }
        } catch {
            Write-Host "Erreur validation resultats: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Resume des tests
Write-Host ("=" * 50) -ForegroundColor Yellow
Write-Host "Resultats: $tests_passed/$total_tests tests reussis" -ForegroundColor Cyan

if ($tests_passed -eq $total_tests) {
    Write-Host "Tous les tests sont passes !" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Certains tests ont echoue" -ForegroundColor Yellow
    exit 1
}