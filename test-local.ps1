# Test script for Qwen2.5-Coder-7B API
# Tests all three endpoints: /health, /generate, /chat

$BASE_URL = "http://localhost:8000"

Write-Host "`n=== Testing Qwen2.5-Coder-7B API ===" -ForegroundColor Cyan

# Test 1: Health Check
Write-Host "`n[1/3] Testing /health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/health" -Method Get
    Write-Host "Status: $($response.status)" -ForegroundColor Green
    Write-Host "Model: $($response.model)"
    Write-Host "Device: $($response.device)"
    Write-Host "DType: $($response.dtype)"
} catch {
    Write-Host "Health check failed: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Code Generation
Write-Host "`n[2/3] Testing /generate endpoint..." -ForegroundColor Yellow
$generateRequest = @{
    prompt = "def fibonacci(n):"
    max_tokens = 256
    temperature = 0.7
    top_p = 0.95
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/generate" -Method Post -Body $generateRequest -ContentType "application/json"
    Write-Host "Generated code:" -ForegroundColor Green
    Write-Host $response.generated_text
    Write-Host "`nFinish reason: $($response.finish_reason)"
} catch {
    Write-Host "Generation failed: $_" -ForegroundColor Red
}

# Test 3: Chat Interface
Write-Host "`n[3/3] Testing /chat endpoint..." -ForegroundColor Yellow
$chatRequest = @{
    messages = @(
        @{
            role = "system"
            content = "You are a helpful coding assistant."
        },
        @{
            role = "user"
            content = "Write a Python function to calculate factorial using recursion."
        }
    )
    max_tokens = 256
    temperature = 0.7
    top_p = 0.95
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/chat" -Method Post -Body $chatRequest -ContentType "application/json"
    Write-Host "Assistant response:" -ForegroundColor Green
    Write-Host $response.message.content
    Write-Host "`nFinish reason: $($response.finish_reason)"
} catch {
    Write-Host "Chat failed: $_" -ForegroundColor Red
}

Write-Host "`n=== All tests completed ===" -ForegroundColor Cyan
