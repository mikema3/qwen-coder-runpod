# RunPod Serverless Deployment Guide

Complete guide to deploy Qwen2.5-Coder-7B on RunPod with **scale-to-zero** (no cost when idle).

## Prerequisites

1. **RunPod Account**: Sign up at https://www.runpod.io/
2. **Docker Image**: `mikema3/qwen-coder-runpod:latest` (already built and available on Docker Hub)
3. **Credits**: Add credits to your RunPod account ($10-20 recommended for testing)

## Cost Breakdown

RunPod Serverless charges **only when your endpoint is actively processing requests**:

| GPU Type | Cost per Second | Cost per Hour (if active) | Typical Cost |
|----------|----------------|---------------------------|--------------|
| RTX 4090 (24GB) | ~$0.000094 | ~$0.34/hour | **Recommended** |
| RTX A5000 (24GB) | ~$0.000139 | ~$0.50/hour | Alternative |
| RTX 3090 (24GB) | ~$0.000078 | ~$0.28/hour | Budget option |

**Important**: With scale-to-zero, you pay **$0** when no requests are being processed!

Example monthly costs:
- 100 requests/day (5 seconds each): ~$0.78/month
- 1,000 requests/day (5 seconds each): ~$7.80/month
- 10,000 requests/day (5 seconds each): ~$78/month

## Step-by-Step Deployment

### Step 1: Create Serverless Endpoint

1. **Go to RunPod Console**: https://www.runpod.io/console/serverless
2. **Click "New Endpoint"**
3. **Configure the endpoint**:

   **Basic Settings:**
   - **Endpoint Name**: `qwen-coder-7b` (or any name you prefer)
   - **Select GPU**: Choose **RTX 4090** (recommended for best price/performance)
   - **Min Workers**: `0` ⚠️ **CRITICAL** - This enables scale-to-zero!
   - **Max Workers**: `1` (start with 1, increase if needed for concurrent requests)

   **Container Configuration:**
   - **Container Image**: `mikema3/qwen-coder-runpod:latest`
   - **Container Disk**: `20 GB` (minimum, increase if pre-downloading model)
   - **Container Registry Credentials**: Leave empty (public image)

   **Environment Variables** (Optional but recommended):
   ```
   HF_TOKEN=your_huggingface_token_here
   MODEL_ID=Qwen/Qwen2.5-Coder-7B
   MAX_LENGTH=4096
   DTYPE=float16
   PORT=8000
   ```
   
   > **Note**: `HF_TOKEN` is optional but recommended to avoid rate limits when downloading the model. Get yours at https://huggingface.co/settings/tokens (read permission is sufficient).

   **Advanced Settings:**
   - **Idle Timeout**: `5 seconds` (how long to wait before scaling to zero after last request)
   - **Execution Timeout**: `300 seconds` (max time for a single request)
   - **GPU Count**: `1`

4. **Click "Deploy"**

### Step 2: Wait for Initialization

- RunPod will pull the Docker image (~15GB)
- First startup will download Qwen2.5-Coder-7B model (~14GB) - takes 2-5 minutes
- Status will show "Ready" when complete

### Step 3: Get Your Endpoint URL

Once deployed, you'll see:
- **Endpoint ID**: Something like `abcd1234-5678-90ef-ghij-klmnopqrstuv`
- **Endpoint URL**: `https://api.runpod.ai/v2/{endpoint_id}/run` (for async)
- **API Key**: Copy this from your RunPod settings

### Step 4: Test Your Deployment

RunPod uses a different API structure than our FastAPI endpoints. Here's how to call it:

#### Option A: RunPod's Web Interface
1. Go to your endpoint in the RunPod console
2. Click "Test Request"
3. Use the input format below

#### Option B: Using PowerShell

Create a test script `test-runpod.ps1`:

```powershell
# RunPod API configuration
$RUNPOD_API_KEY = "your-runpod-api-key-here"
$ENDPOINT_ID = "your-endpoint-id-here"
$RUNPOD_URL = "https://api.runpod.ai/v2/$ENDPOINT_ID/runsync"

# Test 1: Health Check
Write-Host "`n=== Testing Health Check ===" -ForegroundColor Cyan
$healthRequest = @{
    input = @{
        endpoint = "/health"
        method = "GET"
    }
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $RUNPOD_URL -Method Post `
        -Headers @{Authorization = "Bearer $RUNPOD_API_KEY"} `
        -Body $healthRequest -ContentType "application/json"
    Write-Host "Response:" -ForegroundColor Green
    Write-Host ($response | ConvertTo-Json -Depth 10)
} catch {
    Write-Host "Health check failed: $_" -ForegroundColor Red
}

# Test 2: Code Generation
Write-Host "`n=== Testing Code Generation ===" -ForegroundColor Cyan
$generateRequest = @{
    input = @{
        endpoint = "/generate"
        method = "POST"
        body = @{
            prompt = "def fibonacci(n):"
            max_tokens = 256
            temperature = 0.7
            top_p = 0.95
        }
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri $RUNPOD_URL -Method Post `
        -Headers @{Authorization = "Bearer $RUNPOD_API_KEY"} `
        -Body $generateRequest -ContentType "application/json"
    Write-Host "Generated Code:" -ForegroundColor Green
    Write-Host $response.output.generated_text
} catch {
    Write-Host "Generation failed: $_" -ForegroundColor Red
}
```

**Important**: RunPod wraps your FastAPI endpoints. The actual request format is:
```json
{
  "input": {
    "endpoint": "/generate",
    "method": "POST", 
    "body": {
      "prompt": "your code here",
      "max_tokens": 256
    }
  }
}
```

### Step 5: Monitor Costs

1. Go to **RunPod Console → Billing**
2. Check **Usage Statistics** for your endpoint
3. Monitor:
   - Active time (when requests are being processed)
   - Idle time (should be 99%+ with scale-to-zero)
   - Total requests
   - Average execution time

## Alternative: Direct FastAPI Access (Advanced)

If you want to access the FastAPI endpoints directly without RunPod's wrapper:

1. Use **RunPod Pods** (not Serverless) - but this does NOT scale to zero
2. Or modify the RunPod handler to proxy requests directly

For most use cases, the RunPod Serverless wrapper is fine and provides better integration.

## Troubleshooting

### Issue: Endpoint shows "Error" status
- Check logs in RunPod console
- Verify Docker image is accessible: https://hub.docker.com/r/mikema3/qwen-coder-runpod
- Ensure GPU has enough VRAM (need 24GB for 7B model in FP16)

### Issue: Model download timeout
- Increase **Execution Timeout** to 600 seconds
- Or pre-bake model into Docker image (see Dockerfile comments)
- Add `HF_TOKEN` environment variable to avoid rate limits

### Issue: High costs
- Verify **Min Workers = 0** (scale-to-zero enabled)
- Check **Idle Timeout** is set to 5-10 seconds
- Monitor active time in billing dashboard

### Issue: Slow cold starts
- First request after scale-to-zero takes 30-60 seconds (model loading)
- To reduce: Pre-download model into Docker image (increases image size to ~30GB)
- Or use **Min Workers = 1** (keeps one instance always warm, but costs ~$0.34/hour 24/7)

## Cost Optimization Tips

1. **Use scale-to-zero**: Set Min Workers = 0
2. **Short idle timeout**: 5-10 seconds is optimal
3. **Batch requests**: Process multiple prompts in one request when possible
4. **Choose right GPU**: RTX 4090 offers best price/performance for 7B models
5. **Monitor usage**: Check billing dashboard weekly

## Next Steps

- Integrate the endpoint into your application
- Set up monitoring and alerts
- Consider caching responses for common queries
- Benchmark different temperature/top_p settings for your use case

## Support

- **RunPod Docs**: https://docs.runpod.io/
- **RunPod Discord**: https://discord.gg/runpod
- **GitHub Issues**: https://github.com/mikema3/qwen-coder-runpod/issues
