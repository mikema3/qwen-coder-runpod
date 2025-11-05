# Optimized Dockerfile for Qwen2.5-Coder-7B on RunPod
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    MODEL_ID=Qwen/Qwen2.5-Coder-7B \
    MAX_LENGTH=4096 \
    DTYPE=float16 \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY app_runpod.py app.py

# Pre-download the model at build time (optional, makes startup faster)
# Uncomment if you want model baked into image
# ARG HF_TOKEN
# ENV HF_TOKEN=${HF_TOKEN}
# RUN python3 -c "from transformers import AutoTokenizer, AutoModelForCausalLM; \
#     AutoTokenizer.from_pretrained('${MODEL_ID}'); \
#     AutoModelForCausalLM.from_pretrained('${MODEL_ID}', device_map='cpu', torch_dtype='auto')"
# ENV HF_TOKEN=""

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the RunPod serverless handler
CMD ["python3", "app.py"]
