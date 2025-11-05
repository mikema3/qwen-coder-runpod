# Test script for RunPod Qwen2.5-Coder-7B endpoint
# Uses environment variable RUNPOD_API_KEY
$RUNPOD_API_KEY = $env:RUNPOD_API_KEY
$ENDPOINT_ID = "wala78qzvi3o8d"

$RUNPOD_URL = "https://api.runpod.ai/v2/$ENDPOINT_ID/run"

Write-Host "`n=== Testing RunPod Qwen2.5-Coder-7B Endpoint ===" -ForegroundColor Cyan
Write-Host "Endpoint: $ENDPOINT_ID" -ForegroundColor Gray
Write-Host "URL: $RUNPOD_URL`n" -ForegroundColor Gray

# Test 1: Health Check
Write-Host "[1/3] Testing Health Check..." -ForegroundColor Yellow
$healthRequest = @{
    input = @{
        prompt = "Hello"
    }
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $RUNPOD_URL -Method Post `
        -Headers @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $RUNPOD_API_KEY"
        } `
        -Body $healthRequest
    
    Write-Host "Status: SUCCESS" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Gray
    Write-Host ($response | ConvertTo-Json -Depth 10)
} catch {
    Write-Host "Health check failed: $_" -ForegroundColor Red
    Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Code Generation
Write-Host "`n[2/3] Testing Code Generation..." -ForegroundColor Yellow
$generateRequest = @{
    input = @{
        prompt = "def fibonacci(n):"
        max_tokens = 256
        temperature = 0.7
        top_p = 0.95
    }
} | ConvertTo-Json

try {
    Write-Host "Sending request... (this may take 30-60 seconds for first request)" -ForegroundColor Gray
    $response = Invoke-RestMethod -Uri $RUNPOD_URL -Method Post `
        -Headers @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $RUNPOD_API_KEY"
        } `
        -Body $generateRequest -TimeoutSec 120
    
    Write-Host "Generated Code:" -ForegroundColor Green
    if ($response.output) {
        Write-Host $response.output
    } else {
        Write-Host ($response | ConvertTo-Json -Depth 10)
    }
} catch {
    Write-Host "Generation failed: $_" -ForegroundColor Red
    Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Python Function Request
Write-Host "`n[3/3] Testing Python Function Generation..." -ForegroundColor Yellow
$pythonRequest = @{
    input = @{
        prompt = "# Write a Python function to calculate factorial using recursion`ndef factorial(n):"
        max_tokens = 200
        temperature = 0.7
        top_p = 0.95
    }
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $RUNPOD_URL -Method Post `
        -Headers @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $RUNPOD_API_KEY"
        } `
        -Body $pythonRequest -TimeoutSec 120
    
    Write-Host "Generated Function:" -ForegroundColor Green
    if ($response.output) {
        Write-Host $response.output
    } else {
        Write-Host ($response | ConvertTo-Json -Depth 10)
    }
} catch {
    Write-Host "Python generation failed: $_" -ForegroundColor Red
    Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Testing Complete ===" -ForegroundColor Cyan
Write-Host "`nNote: Check RunPod console for billing/usage stats" -ForegroundColor Yellow
