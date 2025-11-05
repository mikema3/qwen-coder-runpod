"""
Qwen2.5-Coder-7B Handler for RunPod Serverless
Processes code completion and chat requests using Qwen2.5-Coder-7B model
"""
import os
import logging
from typing import Dict, Any

import torch
import runpod
from transformers import AutoTokenizer, AutoModelForCausalLM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen2.5-Coder-7B")
MAX_LENGTH = int(os.getenv("MAX_LENGTH", "4096"))
DTYPE = os.getenv("DTYPE", "float16")

# Global model and tokenizer
model = None
tokenizer = None
device = None


def load_model():
    """Load model on startup"""
    global model, tokenizer, device
    
    logger.info(f"Loading model {MODEL_ID}...")
    
    # Determine device
    if torch.cuda.is_available():
        device = "cuda"
        dtype = torch.float16 if DTYPE == "float16" else torch.float32
        logger.info(f"CUDA available - using GPU: {torch.cuda.get_device_name(0)}")
    else:
        device = "cpu"
        dtype = torch.float32
        logger.info("CUDA not available - using CPU")
    
    # Load tokenizer
    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    
    # Load model
    logger.info(f"Loading model with dtype={DTYPE}, device={device}...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=dtype,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True
    )
    
    if device == "cpu":
        model = model.to(device)
    
    model.eval()
    logger.info(f"Model loaded successfully on {device}")


def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod handler function
    Receives job from queue, processes it, returns output
    """
    try:
        job_input = job.get("input", {})
        
        # Extract parameters
        prompt = job_input.get("prompt", "")
        max_tokens = job_input.get("max_tokens", 512)
        temperature = job_input.get("temperature", 0.7)
        top_p = job_input.get("top_p", 0.95)
        
        if not prompt:
            return {"error": "No prompt provided"}
        
        logger.info(f"Processing prompt: {prompt[:50]}...")
        
        # Tokenize input
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_LENGTH - max_tokens
        )
        
        if device == "cuda":
            inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Generate
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=temperature > 0,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        
        # Decode
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the new generation (remove prompt)
        completion = generated_text[len(prompt):]
        
        logger.info(f"Generated {len(completion)} characters")
        
        return {
            "generated_text": completion,
            "prompt": prompt,
            "model": MODEL_ID,
            "finish_reason": "stop" if len(completion) < max_tokens else "length"
        }
        
    except Exception as e:
        logger.error(f"Error processing job: {str(e)}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Load model before starting handler
    load_model()
    
    # Start RunPod serverless handler
    logger.info("Starting RunPod serverless handler...")
    runpod.serverless.start({"handler": handler})
