"""
Qwen2.5-Coder-7B FastAPI Server for RunPod
Serves code completion and chat endpoints using Qwen2.5-Coder-7B model
"""
import os
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
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
PORT = int(os.getenv("PORT", "8000"))

# Global model and tokenizer
model = None
tokenizer = None
device = None


# Request/Response Models
class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Code prompt to complete")
    max_tokens: int = Field(512, ge=1, le=4096, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(0.95, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    stop: Optional[List[str]] = Field(None, description="Stop sequences")


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    max_tokens: int = Field(512, ge=1, le=4096, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(0.95, ge=0.0, le=1.0, description="Nucleus sampling parameter")


class GenerateResponse(BaseModel):
    generated_text: str
    prompt: str
    model: str
    finish_reason: str


class ChatResponse(BaseModel):
    message: ChatMessage
    model: str
    finish_reason: str


class HealthResponse(BaseModel):
    status: str
    model: str
    device: str
    dtype: str


# Load model on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
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
    
    yield
    
    # Cleanup
    logger.info("Shutting down...")
    del model
    del tokenizer
    if device == "cuda":
        torch.cuda.empty_cache()


# Create FastAPI app
app = FastAPI(
    title="Qwen2.5-Coder-7B API",
    description="Code completion and chat API powered by Qwen2.5-Coder-7B",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if model is not None else "loading",
        model=MODEL_ID,
        device=str(device),
        dtype=DTYPE
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate_code(request: GenerateRequest):
    """Generate code completion from prompt"""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    
    try:
        logger.info(f"Generating completion for prompt: {request.prompt[:50]}...")
        
        # Tokenize input
        inputs = tokenizer(
            request.prompt,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_LENGTH - request.max_tokens
        )
        
        if device == "cuda":
            inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Generate
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=request.temperature > 0,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        
        # Decode
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the new generation (remove prompt)
        completion = generated_text[len(request.prompt):]
        
        logger.info(f"Generated {len(completion)} characters")
        
        return GenerateResponse(
            generated_text=completion,
            prompt=request.prompt,
            model=MODEL_ID,
            finish_reason="stop" if len(completion) < request.max_tokens else "length"
        )
        
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat-based code assistance"""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    
    try:
        logger.info(f"Processing chat with {len(request.messages)} messages")
        
        # Format messages using Qwen chat template
        if hasattr(tokenizer, "apply_chat_template"):
            # Use official chat template if available
            formatted_prompt = tokenizer.apply_chat_template(
                [{"role": m.role, "content": m.content} for m in request.messages],
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            # Fallback: simple concatenation
            formatted_prompt = ""
            for msg in request.messages:
                if msg.role == "system":
                    formatted_prompt += f"System: {msg.content}\n\n"
                elif msg.role == "user":
                    formatted_prompt += f"User: {msg.content}\n\n"
                elif msg.role == "assistant":
                    formatted_prompt += f"Assistant: {msg.content}\n\n"
            formatted_prompt += "Assistant:"
        
        # Tokenize
        inputs = tokenizer(
            formatted_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_LENGTH - request.max_tokens
        )
        
        if device == "cuda":
            inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Generate
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=request.temperature > 0,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        
        # Decode
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract assistant response
        response_text = generated_text[len(formatted_prompt):].strip()
        
        logger.info(f"Generated chat response: {len(response_text)} characters")
        
        return ChatResponse(
            message=ChatMessage(role="assistant", content=response_text),
            model=MODEL_ID,
            finish_reason="stop" if len(response_text) < request.max_tokens else "length"
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
