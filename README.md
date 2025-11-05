# Qwen2.5-Coder-7B on RunPod Serverless

Deploy Qwen2.5-Coder-7B language model on RunPod with GPU auto-scaling and scale-to-zero.

## Features

- ✅ **Qwen2.5-Coder-7B** - State-of-the-art 7B parameter coding model
- ✅ **RunPod Serverless** - Pay only when running, auto scale-to-zero
- ✅ **FastAPI** - High-performance REST API
- ✅ **GPU Optimized** - FP16 inference on single GPU (RTX 4090, A40, etc.)
- ✅ **Docker** - Pre-built image ready to deploy
- ✅ **Public GitHub** - Open source, easy to fork and customize

## Quick Start

### Deploy to RunPod (Easiest)

1. **Get Docker Image:**
   ```
   docker.io/YOUR_USERNAME/qwen-coder-runpod:latest
   ```

2. **Deploy on RunPod:**
   - Go to [RunPod Serverless](https://www.runpod.io/console/serverless)
   - Click "New Endpoint"
   - Select GPU: RTX 4090 (24GB) or A40 (48GB)
   - Container Image: `YOUR_USERNAME/qwen-coder-runpod:latest`
   - Container Disk: 20GB
   - Click "Deploy"

3. **Test Your Endpoint:**
   ```bash
   curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "input": {
         "prompt": "Write a Python function to calculate fibonacci numbers",
         "max_tokens": 256
       }
     }'
   ```

## API Endpoints

### POST /generate

Generate code completions.

**Request:**
```json
{
  "prompt": "def fibonacci(n):",
  "max_tokens": 200,
  "temperature": 0.7,
  "top_p": 0.95
}
```

**Response:**
```json
{
  "generated_text": "def fibonacci(n):\n    if n <= 1:\n        return n\n    ...",
  "tokens_generated": 45
}
```

### POST /chat

Chat-based code assistance.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "How do I sort a list in Python?"}
  ],
  "max_tokens": 200
}
```

**Response:**
```json
{
  "response": "To sort a list in Python, you can use the built-in `sort()` method...",
  "tokens_generated": 38
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "model": "Qwen/Qwen2.5-Coder-7B",
  "gpu_available": true,
  "device": "cuda"
}
```

## Costs on RunPod

**GPU Pricing (scale-to-zero):**
- RTX 4090 (24GB): $0.34/hour
- A40 (48GB): $0.59/hour
- A100 (40GB): $1.89/hour

**Example costs:**
- 1,000 requests/day @ 2 sec each: ~$0.19/day ($5.70/month)
- Idle time: $0.00 (scales to zero!)

**vs Always-On:**
- RTX 4090 24/7: $244/month
- With scale-to-zero: **$5-20/month** (95% savings!)

## Local Development

### Prerequisites

- Docker
- NVIDIA GPU (for local testing)
- NVIDIA Container Toolkit

### Build and Test Locally

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/qwen-coder-runpod.git
cd qwen-coder-runpod

# Build Docker image
docker build -t qwen-coder-runpod:latest .

# Run locally (requires NVIDIA GPU)
docker run --gpus all -p 8000:8000 qwen-coder-runpod:latest

# Test the API
curl http://localhost:8000/health

# Test generation
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "def hello_world():",
    "max_tokens": 50
  }'
```

## Model Information

**Qwen2.5-Coder-7B:**
- Parameters: 7 billion
- Context length: 128K tokens (we use 4K by default for speed)
- Languages: Python, Java, C++, JavaScript, and 80+ more
- License: Apache 2.0
- Paper: [Qwen2.5-Coder Technical Report](https://arxiv.org/abs/2409.12186)

**Performance:**
- HumanEval: 61.6%
- MBPP: 70.5%
- Top-tier code generation quality

## Repository Structure

```
qwen-coder-runpod/
├── Dockerfile              # Container definition
├── app.py                  # FastAPI application
├── requirements.txt        # Python dependencies
├── .github/
│   └── workflows/
│       └── docker-build.yml # Auto-build Docker images
├── .dockerignore          # Docker build exclusions
├── .gitignore             # Git exclusions
├── LICENSE                # Apache 2.0 license
└── README.md              # This file
```

## GitHub Actions

Automatically builds and pushes Docker images to Docker Hub on every push to `main`.

**Setup:**
1. Add Docker Hub secrets to GitHub:
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_TOKEN`

2. Push to main branch - image automatically builds and deploys!

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_ID` | `Qwen/Qwen2.5-Coder-7B` | HuggingFace model ID |
| `MAX_LENGTH` | `4096` | Max context length |
| `DTYPE` | `float16` | Model precision (float16 for speed) |
| `PORT` | `8000` | API server port |
| `HF_TOKEN` | - | HuggingFace token (optional, for gated models) |

## Advanced Configuration

### Use Larger Context

```bash
docker run --gpus all -p 8000:8000 \
  -e MAX_LENGTH=8192 \
  qwen-coder-runpod:latest
```

### Use Different Model

```bash
docker run --gpus all -p 8000:8000 \
  -e MODEL_ID=Qwen/Qwen2.5-Coder-14B \
  qwen-coder-runpod:latest
```

## Troubleshooting

**Out of Memory:**
- Use smaller max_length (2048 or 4096)
- Reduce batch size to 1
- Use RTX 4090 or larger GPU

**Slow Generation:**
- Check GPU utilization
- Reduce max_tokens in requests
- Use FP16 (already default)

**Model Download Fails:**
- Add HF_TOKEN environment variable
- Check internet connectivity
- Verify model ID is correct

## Contributing

Pull requests welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

Apache 2.0 - see [LICENSE](LICENSE) file.

## Acknowledgments

- [Qwen Team](https://huggingface.co/Qwen) for the amazing models
- [RunPod](https://runpod.io) for serverless GPU infrastructure
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/YOUR_USERNAME/qwen-coder-runpod/issues)
- RunPod Discord: [Get help with deployment](https://discord.gg/runpod)
