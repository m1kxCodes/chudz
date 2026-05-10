from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import uuid
from datetime import datetime
import torch
try:
    import torch_directml
except ImportError:
    torch_directml = None
except Exception as e:
    print(f"Note: torch-directml is unavailable: {e}")
    torch_directml = None
import diffusers
import numpy as np
import configparser
import gc
from diffusers import (
    AutoPipelineForImage2Image,
    AutoPipelineForText2Image,
    DPMSolverMultistepScheduler,
    TextToVideoSDPipeline,
)
import imageio.v2 as imageio
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from PIL import Image
import io
import asyncio
from pathlib import Path

app = FastAPI(title="NoFilters Image Generator", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
CONFIG = configparser.ConfigParser()
CONFIG.read(PROJECT_ROOT / "config.ini")

def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()

GALLERY_DIR = resolve_project_path(os.getenv("GALLERY_PATH", "gallery"))
GALLERY_DIR.mkdir(parents=True, exist_ok=True)
SAFE_MODEL_ID = "RunDiffusion/Juggernaut-XL-v9"
NSFW_MODEL_BIG_LUST = "John6666/big-lust-v16-sdxl"
NSFW_MODEL_OPTION2 = "stabilityai/stable-diffusion-2-1"
VIDEO_MODEL_ID = os.getenv("VIDEO_MODEL_ID", "damo-vilab/text-to-video-ms-1.7b")
CURRENT_MODEL_ID = SAFE_MODEL_ID
CURRENT_NSFW_MODE = False
PROMPT_ENHANCER_MODEL_ID = os.getenv("PROMPT_ENHANCER_MODEL", "google/flan-t5-base")

def config_value(section: str, option: str, default: str) -> str:
    scoped_key = f"NOFILTERS_{section}_{option}".upper()
    simple_key = f"NOFILTERS_{option}".upper()
    return os.getenv(scoped_key) or os.getenv(simple_key) or CONFIG.get(section, option, fallback=default)

def config_bool(section: str, option: str, default: bool) -> bool:
    value = config_value(section, option, str(default)).strip().lower()
    return value in {"1", "true", "yes", "on"}

def normalize_device_name(value: str) -> str:
    requested = (value or "auto").strip().lower()
    aliases = {
        "dml": "directml",
        "direct-ml": "directml",
        "nvidia": "cuda",
        "gpu": "auto",
    }
    return aliases.get(requested, requested)

RAW_REQUESTED_DEVICE = config_value("DEVICE", "device", "auto").strip().lower()
REQUESTED_DEVICE = normalize_device_name(RAW_REQUESTED_DEVICE)
DIRECTML_DEVICE_INDEX = config_value("DEVICE", "directml_device_index", "auto").strip().lower()
USE_FLOAT16 = config_bool("OPTIMIZATION", "use_float16", True)

def clean_device_name(value) -> str:
    return str(value).replace("\x00", "").strip()

def get_directml_device_index(prefer_amd: bool = False) -> int:
    if DIRECTML_DEVICE_INDEX not in {"", "auto", "default"}:
        try:
            return int(DIRECTML_DEVICE_INDEX)
        except ValueError:
            print(f"Note: invalid DirectML device index '{DIRECTML_DEVICE_INDEX}', using auto selection.")

    if prefer_amd and hasattr(torch_directml, "device_count") and hasattr(torch_directml, "device_name"):
        for index in range(torch_directml.device_count()):
            name = clean_device_name(torch_directml.device_name(index)).lower()
            if "amd" in name or "radeon" in name:
                return index

    return torch_directml.default_device() if hasattr(torch_directml, "default_device") else 0

def get_directml_device(prefer_amd: bool = False):
    if torch_directml is None:
        return None, None

    try:
        if hasattr(torch_directml, "is_available") and not torch_directml.is_available():
            return None, None

        device_index = get_directml_device_index(prefer_amd)
        try:
            device = torch_directml.device(device_index)
        except TypeError:
            device = torch_directml.device()

        device_name = "DirectML GPU"
        if hasattr(torch_directml, "device_name"):
            try:
                device_name = clean_device_name(torch_directml.device_name(device_index))
            except Exception:
                device_name = "DirectML GPU"
        return device, device_name
    except Exception as e:
        print(f"Note: DirectML device unavailable: {e}")
        return None, None

def select_device():
    if REQUESTED_DEVICE == "cpu":
        return torch.device("cpu"), "cpu", "CPU"

    if REQUESTED_DEVICE == "cuda":
        if torch.cuda.is_available():
            return torch.device("cuda"), "cuda", torch.cuda.get_device_name(0)
        print("Note: CUDA was requested but is not available, falling back to CPU.")
        return torch.device("cpu"), "cpu", "CPU"

    if REQUESTED_DEVICE in {"amd", "directml"}:
        directml_device, directml_name = get_directml_device(prefer_amd=REQUESTED_DEVICE == "amd")
        if directml_device is not None:
            return directml_device, "directml", directml_name
        print("Note: DirectML was requested but torch-directml is unavailable, falling back to CPU.")
        return torch.device("cpu"), "cpu", "CPU"

    if torch.cuda.is_available():
        return torch.device("cuda"), "cuda", torch.cuda.get_device_name(0)

    directml_device, directml_name = get_directml_device(prefer_amd=True)
    if directml_device is not None:
        return directml_device, "directml", directml_name

    return torch.device("cpu"), "cpu", "CPU"

TORCH_DEVICE, DEVICE, DEVICE_NAME = select_device()

def is_cuda_device() -> bool:
    return DEVICE == "cuda"

def is_gpu_device() -> bool:
    return DEVICE in {"cuda", "directml"}

def clear_accelerator_cache():
    gc.collect()
    if is_cuda_device():
        torch.cuda.empty_cache()
    elif DEVICE == "directml" and torch_directml is not None and hasattr(torch_directml, "empty_cache"):
        torch_directml.empty_cache()

def make_generator(seed: int):
    generator_device = "cuda" if is_cuda_device() else "cpu"
    return torch.Generator(device=generator_device).manual_seed(seed)

# Some newer SDXL checkpoints name this scheduler in model_index.json, but the
# pinned Diffusers version does not expose it. DPMSolver is compatible enough for
# these configs and is already the scheduler this app standardizes on.
if not hasattr(diffusers, "EDMDPMSolverMultistepScheduler"):
    diffusers.EDMDPMSolverMultistepScheduler = DPMSolverMultistepScheduler

# Global pipeline instances
text2img_pipe = None
img2img_pipe = None
inpaint_pipe = None
video_pipe = None
prompt_enhancer_tokenizer = None
prompt_enhancer_model = None

# Pydantic models
class GenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    num_inference_steps: int = 30
    guidance_scale: float = 6.5
    height: int = 1024
    width: int = 1024
    num_images: int = 1
    nsfw_mode: Optional[bool] = False
    nsfw_model: Optional[str] = "big_lust"  # "big_lust" or "option2"

class VideoGenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    num_inference_steps: int = 25
    guidance_scale: float = 9.0
    height: int = 320
    width: int = 576
    num_frames: int = 16
    fps: int = 8

class PromptEnhanceRequest(BaseModel):
    prompt: str
    style: Optional[str] = "cinematic"

class ImageVariationRequest(BaseModel):
    prompt: Optional[str] = "a beautiful high quality image"
    negative_prompt: Optional[str] = ""
    strength: float = 0.75
    num_inference_steps: int = 50
    guidance_scale: float = 7.5
    num_images: int = 1
    nsfw_mode: Optional[bool] = False
    nsfw_model: Optional[str] = "big_lust"

class InpaintRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    strength: float = 0.75
    num_inference_steps: int = 50
    guidance_scale: float = 7.5

class ModelSwitchRequest(BaseModel):
    nsfw_mode: bool = False
    nsfw_model: Optional[str] = "big_lust"  # "big_lust" or "option2"

def resolve_image_model_id(nsfw_mode: bool = False, nsfw_model: Optional[str] = "big_lust") -> str:
    if nsfw_mode:
        return NSFW_MODEL_OPTION2 if nsfw_model == "option2" else NSFW_MODEL_BIG_LUST
    return SAFE_MODEL_ID

def load_models(model_id: Optional[str] = None):
    """Load matching text-to-image and image-to-image pipelines."""
    global text2img_pipe, img2img_pipe, inpaint_pipe, video_pipe, CURRENT_MODEL_ID

    model_id = model_id or CURRENT_MODEL_ID
    if text2img_pipe is not None and img2img_pipe is not None and CURRENT_MODEL_ID == model_id:
        return
    
    print(f"Loading models on {DEVICE} ({DEVICE_NAME})...")
    print(f"Model: {model_id}")

    text2img_pipe = None
    img2img_pipe = None
    inpaint_pipe = None

    if is_gpu_device():
        video_pipe = None
        clear_accelerator_cache()

    def load_compatible_scheduler():
        try:
            return DPMSolverMultistepScheduler.from_pretrained(model_id, subfolder="scheduler")
        except Exception as e:
            print(f"Note: could not pre-load DPMSolverMultistepScheduler, using model default: {e}")
            return None

    def configure_pipeline(pipe):
        # Try to configure scheduler - different models may use different schedulers
        try:
            pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
        except Exception as e:
            print(f"Note: DPMSolverMultistepScheduler not compatible, using model's default scheduler: {e}")
            # Keep the original scheduler if DPMSolver isn't compatible
        
        pipe.to(TORCH_DEVICE)
        pipe.enable_attention_slicing()
        return pipe

    def build_pipeline_kwargs(torch_dtype, use_safetensors=True, variant=None):
        kwargs = {
            "torch_dtype": torch_dtype,
            "use_safetensors": use_safetensors,
        }
        scheduler = load_compatible_scheduler()
        if scheduler is not None:
            kwargs["scheduler"] = scheduler
        if variant:
            kwargs["variant"] = variant
        return kwargs

    load_attempts = []
    if is_gpu_device() and USE_FLOAT16:
        load_attempts.append(build_pipeline_kwargs(torch.float16, use_safetensors=True, variant="fp16"))
    load_attempts.append(build_pipeline_kwargs(torch.float32, use_safetensors=True))
    load_attempts.append(build_pipeline_kwargs(torch.float32, use_safetensors=None))

    last_error = None
    for kwargs in load_attempts:
        try:
            text2img_pipe = AutoPipelineForText2Image.from_pretrained(model_id, **kwargs)
            break
        except Exception as e:
            last_error = e
            variant = f" variant={kwargs['variant']}" if "variant" in kwargs else ""
            print(f"Note: text-to-image load failed with dtype={kwargs['torch_dtype']}{variant}: {e}")
    else:
        raise last_error

    text2img_pipe = configure_pipeline(text2img_pipe)
    if hasattr(text2img_pipe, "safety_checker"):
        text2img_pipe.safety_checker = None
        text2img_pipe.register_to_config(requires_safety_checker=False)

    img2img_pipe = AutoPipelineForImage2Image.from_pipe(text2img_pipe)
    img2img_pipe = configure_pipeline(img2img_pipe)
    if hasattr(img2img_pipe, "safety_checker"):
        img2img_pipe.safety_checker = None
        img2img_pipe.register_to_config(requires_safety_checker=False)

    CURRENT_MODEL_ID = model_id
    
    print("Models loaded successfully!")

def unload_image_models():
    """Release image pipelines before loading the video model on constrained GPUs."""
    global text2img_pipe, img2img_pipe, inpaint_pipe

    text2img_pipe = None
    img2img_pipe = None
    inpaint_pipe = None
    if is_gpu_device():
        clear_accelerator_cache()

def load_video_model():
    """Load the text-to-video model on first use."""
    global video_pipe

    if video_pipe:
        return video_pipe

    if is_gpu_device():
        unload_image_models()

    print(f"Loading video model on {DEVICE} ({DEVICE_NAME})...")
    print(f"Video model: {VIDEO_MODEL_ID}")

    pipeline_kwargs = {
        "torch_dtype": torch.float16 if is_gpu_device() and USE_FLOAT16 else torch.float32,
    }

    if is_gpu_device() and USE_FLOAT16:
        pipeline_kwargs["variant"] = "fp16"

    try:
        pipe = TextToVideoSDPipeline.from_pretrained(VIDEO_MODEL_ID, **pipeline_kwargs)
    except Exception as e:
        if "variant" not in pipeline_kwargs:
            raise
        print(f"Note: video fp16 variant not available, loading default weights: {e}")
        del pipeline_kwargs["variant"]
        pipe = TextToVideoSDPipeline.from_pretrained(VIDEO_MODEL_ID, **pipeline_kwargs)

    try:
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    except Exception as e:
        print(f"Note: video scheduler kept as model default: {e}")

    pipe.enable_attention_slicing()
    if hasattr(pipe, "enable_vae_slicing"):
        pipe.enable_vae_slicing()

    if is_cuda_device():
        try:
            pipe.enable_model_cpu_offload()
            print("Video model CPU offload enabled.")
        except Exception as e:
            print(f"Note: video CPU offload unavailable, moving model to CUDA: {e}")
            pipe.to(TORCH_DEVICE)
    else:
        pipe.to(TORCH_DEVICE)

    video_pipe = pipe
    print("Video model loaded successfully!")
    return video_pipe

def prepare_video_frames(frames):
    """Normalize pipeline output into an imageio-compatible RGB frame list."""
    if isinstance(frames, torch.Tensor):
        frames = frames.detach().cpu()
        if frames.ndim == 5:
            frames = frames[0]
        if frames.ndim == 4 and frames.shape[0] in (1, 3, 4):
            frames = frames.permute(1, 2, 3, 0)
        elif frames.ndim == 4 and frames.shape[1] in (1, 3, 4):
            frames = frames.permute(0, 2, 3, 1)
        frames = frames.numpy()

    if isinstance(frames, np.ndarray):
        if frames.ndim == 5:
            frames = frames[0]
        if frames.ndim == 4:
            if frames.shape[1] in (1, 3, 4) and frames.shape[-1] not in (1, 3, 4):
                frames = np.moveaxis(frames, 1, -1)
            frames = list(frames)
        elif frames.ndim == 3:
            frames = [frames]

    frame_list = list(frames) if frames is not None else []
    if len(frame_list) == 1 and np.asarray(frame_list[0]).ndim == 4:
        return prepare_video_frames(frame_list[0])
    if len(frame_list) < 2:
        raise ValueError("Video generation returned fewer than 2 frames")

    prepared = []
    for frame in frame_list:
        array = np.asarray(frame)
        if array.ndim == 4:
            prepared.extend(prepare_video_frames(array))
            continue
        if array.ndim == 2:
            array = np.stack([array, array, array], axis=-1)
        if array.ndim != 3:
            raise ValueError(f"Unexpected video frame shape: {array.shape}")
        if array.shape[0] in (1, 3, 4) and array.shape[-1] not in (1, 3, 4):
            array = np.moveaxis(array, 0, -1)
        if array.shape[-1] == 1:
            array = np.repeat(array, 3, axis=-1)
        elif array.shape[-1] == 4:
            array = array[:, :, :3]
        elif array.shape[-1] != 3:
            raise ValueError(f"Unexpected video frame channels: {array.shape[-1]}")

        if array.dtype != np.uint8:
            if array.size and float(np.nanmax(array)) <= 1.0:
                array = array * 255
            array = np.nan_to_num(array, nan=0.0, posinf=255.0, neginf=0.0)
            array = np.clip(array, 0, 255).astype(np.uint8)
        prepared.append(np.ascontiguousarray(array))

    return prepared

def save_video_file(filepath: Path, frames, fps: int):
    """Write browser-playable MP4, falling back to imageio defaults if needed."""
    try:
        imageio.mimsave(
            str(filepath),
            frames,
            fps=fps,
            macro_block_size=8,
            codec="libx264",
            pixelformat="yuv420p",
        )
    except Exception as first_error:
        if filepath.exists():
            filepath.unlink()
        print(f"Note: libx264 video export failed, trying default ffmpeg settings: {first_error}")
        imageio.mimsave(str(filepath), frames, fps=fps, macro_block_size=8)

def ensure_image_models_loaded():
    if not text2img_pipe or not img2img_pipe:
        load_models(CURRENT_MODEL_ID)

def parse_variation_request(request_data: Optional[str]) -> ImageVariationRequest:
    if not request_data:
        return ImageVariationRequest()
    try:
        return ImageVariationRequest.model_validate_json(request_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid variation request data: {e}")

def prepare_variation_image(image: Image.Image, max_side: int = 1024) -> Image.Image:
    width, height = image.size
    if width <= 0 or height <= 0:
        raise HTTPException(status_code=400, detail="Uploaded image has invalid dimensions")

    scale = min(1.0, max_side / max(width, height))
    target_width = max(64, int(width * scale))
    target_height = max(64, int(height * scale))
    target_width -= target_width % 8
    target_height -= target_height % 8

    if (target_width, target_height) == image.size:
        return image
    return image.resize((target_width, target_height), Image.Resampling.LANCZOS)

def validate_variation_request(request: ImageVariationRequest):
    if request.strength <= 0 or request.strength > 1:
        raise HTTPException(status_code=400, detail="strength must be greater than 0 and at most 1")
    if request.num_inference_steps < 1 or request.num_inference_steps > 150:
        raise HTTPException(status_code=400, detail="num_inference_steps must be between 1 and 150")
    if request.guidance_scale < 1 or request.guidance_scale > 20:
        raise HTTPException(status_code=400, detail="guidance_scale must be between 1 and 20")
    if request.num_images < 1 or request.num_images > 10:
        raise HTTPException(status_code=400, detail="num_images must be between 1 and 10")

def load_prompt_enhancer():
    """Load the prompt enhancer on CPU the first time it is requested."""
    global prompt_enhancer_tokenizer, prompt_enhancer_model

    if prompt_enhancer_tokenizer and prompt_enhancer_model:
        return prompt_enhancer_tokenizer, prompt_enhancer_model

    print(f"Loading prompt enhancer model: {PROMPT_ENHANCER_MODEL_ID}")
    prompt_enhancer_tokenizer = AutoTokenizer.from_pretrained(PROMPT_ENHANCER_MODEL_ID)
    prompt_enhancer_model = AutoModelForSeq2SeqLM.from_pretrained(PROMPT_ENHANCER_MODEL_ID)
    prompt_enhancer_model.to("cpu")
    prompt_enhancer_model.eval()
    print("Prompt enhancer loaded successfully!")
    return prompt_enhancer_tokenizer, prompt_enhancer_model

def fallback_enhance_prompt(base_prompt: str, style: str):
    """Deterministic fallback if the AI enhancer cannot run."""
    style_phrases = {
        "cinematic": "cinematic composition, dramatic lighting, rich atmosphere, highly detailed, sharp focus",
        "photo": "realistic professional photography, natural lighting, detailed textures, shallow depth of field, sharp focus",
        "portrait": "professional portrait, expressive face, detailed eyes, flattering key light, realistic skin texture, sharp focus",
        "anime": "high quality anime illustration, expressive character design, clean linework, vibrant colors, detailed background",
        "concept": "high-end concept art, intricate design, dynamic composition, detailed environment, polished digital painting",
        "product": "premium product photography, clean studio lighting, crisp details, realistic materials, commercial quality",
    }
    style_phrase = style_phrases.get(style, style_phrases["cinematic"])
    quality_phrase = (
        "Pony Diffusion V6 XL, high resolution, coherent subject, balanced composition, "
        "accurate anatomy, detailed background, professional color grading"
    )
    return f"{base_prompt}, {style_phrase}, {quality_phrase}"

def clean_enhanced_prompt(text: str, base_prompt: str, style: str):
    cleaned = " ".join(text.replace("\n", ", ").replace("Prompt:", "").split())
    cleaned = cleaned.strip(" ,.:;\"'")

    if len(cleaned) < 40 or cleaned.lower() == base_prompt.lower():
        cleaned = fallback_enhance_prompt(base_prompt, style)
    elif base_prompt.lower() not in cleaned.lower():
        cleaned = f"{base_prompt}, {cleaned}"

    return cleaned[:900]

def generate_ai_enhanced_prompt(base_prompt: str, style: str):
    tokenizer, model = load_prompt_enhancer()
    instruction = (
        "Rewrite this image prompt for Pony Diffusion V6 XL. "
        "Return one vivid comma-separated prompt only. "
        "Keep the original subject and make it more specific, visual, and coherent. "
        "Include subject details, environment, lighting, camera or art direction, composition, and quality terms. "
        "Do not add explanations, labels, or negative prompt terms. "
        f"Style: {style}. "
        f"Prompt: {base_prompt}"
    )

    inputs = tokenizer(
        instruction,
        return_tensors="pt",
        truncation=True,
        max_length=512,
    )
    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=130,
            num_beams=4,
            do_sample=False,
            no_repeat_ngram_size=3,
        )

    generated = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return clean_enhanced_prompt(generated, base_prompt, style)

@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    await asyncio.to_thread(load_models)

@app.get("/")
async def root():
    return {"message": "NoFilters Image Generator API", "device": DEVICE}

@app.get("/status")
async def status():
    """Get generation status and device info"""
    return {
        "device": DEVICE,
        "requested_device": RAW_REQUESTED_DEVICE,
        "gpu_available": is_gpu_device(),
        "gpu_name": DEVICE_NAME if is_gpu_device() else None,
        "model": CURRENT_MODEL_ID,
        "nsfw_mode": CURRENT_NSFW_MODE,
        "video_model": VIDEO_MODEL_ID,
        "video_loaded": video_pipe is not None,
    }

@app.post("/switch-model")
async def switch_model(request: ModelSwitchRequest):
    """Switch between safe and NSFW models"""
    global CURRENT_NSFW_MODE
    
    try:
        model_to_load = resolve_image_model_id(request.nsfw_mode, request.nsfw_model)
        if CURRENT_MODEL_ID != model_to_load or text2img_pipe is None or img2img_pipe is None:
            print(f"Switching to model: {model_to_load}")
            await asyncio.to_thread(load_models, model_to_load)

        CURRENT_NSFW_MODE = bool(request.nsfw_mode)
        
        return {
            "status": "success",
            "model": CURRENT_MODEL_ID,
            "nsfw_mode": CURRENT_NSFW_MODE,
            "message": f"Model switched successfully to {'NSFW mode' if CURRENT_NSFW_MODE else 'Safe mode'}"
        }
    except Exception as e:
        error_msg = str(e)
        print(f"Model switch error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Failed to switch model: {error_msg}")

@app.post("/enhance-prompt")
async def enhance_prompt(request: PromptEnhanceRequest):
    """Use a local AI model to expand a short prompt into a stronger SDXL prompt."""
    base_prompt = " ".join(request.prompt.strip().split())
    if not base_prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    style = (request.style or "cinematic").lower()
    negative = (
        "blurry, low quality, distorted, deformed, bad anatomy, extra limbs, "
        "extra fingers, duplicate subject, text, watermark, logo, cropped, out of frame"
    )

    source = "ai"
    try:
        enhanced = await asyncio.to_thread(generate_ai_enhanced_prompt, base_prompt, style)
    except Exception as e:
        print(f"Prompt enhancer failed, using fallback: {e}")
        enhanced = fallback_enhance_prompt(base_prompt, style)
        source = "fallback"

    return {
        "prompt": enhanced,
        "negative_prompt": negative,
        "style": style,
        "source": source,
        "enhancer_model": PROMPT_ENHANCER_MODEL_ID if source == "ai" else None,
    }

@app.post("/generate")
async def generate_image(request: GenerationRequest):
    """Generate image from text prompt"""
    try:
        # Handle model switching if NSFW mode is specified
        if request.nsfw_mode:
            model_request = ModelSwitchRequest(nsfw_mode=True, nsfw_model=request.nsfw_model)
            await switch_model(model_request)
        elif CURRENT_NSFW_MODE:
            # Switch back to safe mode if not in NSFW mode
            model_request = ModelSwitchRequest(nsfw_mode=False)
            await switch_model(model_request)
        
        if not text2img_pipe:
            await asyncio.to_thread(ensure_image_models_loaded)
        
        def generate():
            generator = make_generator(int(datetime.now().timestamp() * 1000) % (2**31))
            
            images = []
            for i in range(request.num_images):
                image = text2img_pipe(
                    prompt=request.prompt,
                    negative_prompt=request.negative_prompt,
                    num_inference_steps=request.num_inference_steps,
                    guidance_scale=request.guidance_scale,
                    height=request.height,
                    width=request.width,
                    generator=generator
                ).images[0]
                
                images.append(image)
            
            return images
        
        images = await asyncio.to_thread(generate)
        
        # Save images and return URLs
        results = []
        for image in images:
            filename = f"{uuid.uuid4()}.png"
            filepath = GALLERY_DIR / filename
            image.save(filepath)
            results.append({
                "id": filename.replace(".png", ""),
                "url": f"/image/{filename}",
                "filename": filename,
                "prompt": request.prompt
            })
        
        return {"success": True, "images": results}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-batch")
async def generate_batch(request: GenerationRequest):
    """Generate multiple images in batch"""
    try:
        # Handle model switching if NSFW mode is specified
        if request.nsfw_mode:
            model_request = ModelSwitchRequest(nsfw_mode=True, nsfw_model=request.nsfw_model)
            await switch_model(model_request)
        elif CURRENT_NSFW_MODE:
            # Switch back to safe mode if not in NSFW mode
            model_request = ModelSwitchRequest(nsfw_mode=False)
            await switch_model(model_request)
        
        if not text2img_pipe:
            await asyncio.to_thread(ensure_image_models_loaded)
        
        def generate():
            images = []
            for i in range(request.num_images):
                generator = make_generator(i)
                image = text2img_pipe(
                    prompt=request.prompt,
                    negative_prompt=request.negative_prompt,
                    num_inference_steps=request.num_inference_steps,
                    guidance_scale=request.guidance_scale,
                    height=request.height,
                    width=request.width,
                    generator=generator
                ).images[0]
                images.append(image)
            return images
        
        images = await asyncio.to_thread(generate)
        
        results = []
        for image in images:
            filename = f"{uuid.uuid4()}.png"
            filepath = GALLERY_DIR / filename
            image.save(filepath)
            results.append({
                "id": filename.replace(".png", ""),
                "url": f"/image/{filename}",
                "filename": filename,
                "prompt": request.prompt
            })
        
        return {"success": True, "images": results, "total": len(results)}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-video")
async def generate_video(request: VideoGenerationRequest):
    """Generate a short MP4 video from a text prompt."""
    prompt = " ".join(request.prompt.strip().split())
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    if request.num_frames < 2 or request.num_frames > 64:
        raise HTTPException(status_code=400, detail="num_frames must be between 2 and 64")
    if request.fps < 1 or request.fps > 30:
        raise HTTPException(status_code=400, detail="fps must be between 1 and 30")
    if request.num_inference_steps < 1 or request.num_inference_steps > 100:
        raise HTTPException(status_code=400, detail="num_inference_steps must be between 1 and 100")
    if request.guidance_scale < 1 or request.guidance_scale > 20:
        raise HTTPException(status_code=400, detail="guidance_scale must be between 1 and 20")
    if request.height < 256 or request.height > 576 or request.width < 256 or request.width > 1024:
        raise HTTPException(status_code=400, detail="Video width and height are outside the supported range")
    if request.height % 8 != 0 or request.width % 8 != 0:
        raise HTTPException(status_code=400, detail="Video width and height must be divisible by 8")

    try:
        pipe = await asyncio.to_thread(load_video_model)

        def generate():
            generator = make_generator(int(datetime.now().timestamp() * 1000) % (2**31))
            with torch.inference_mode():
                output = pipe(
                    prompt=prompt,
                    negative_prompt=request.negative_prompt or None,
                    num_inference_steps=request.num_inference_steps,
                    guidance_scale=request.guidance_scale,
                    height=request.height,
                    width=request.width,
                    num_frames=request.num_frames,
                    generator=generator,
                    output_type="np",
                )

            filename = f"{uuid.uuid4()}.mp4"
            filepath = GALLERY_DIR / filename
            frames = prepare_video_frames(output.frames)
            try:
                save_video_file(filepath, frames, request.fps)
            except Exception:
                if filepath.exists():
                    filepath.unlink()
                raise
            finally:
                if is_gpu_device():
                    clear_accelerator_cache()
            return filename

        filename = await asyncio.to_thread(generate)
        return {
            "success": True,
            "video": {
                "id": filename.replace(".mp4", ""),
                "url": f"/video/{filename}",
                "filename": filename,
                "prompt": prompt,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/variation")
async def create_variation(file: UploadFile = File(...), request_data: Optional[str] = Form(None)):
    """Create variations of an uploaded image"""
    try:
        variation_request = parse_variation_request(request_data)
        validate_variation_request(variation_request)

        if variation_request.nsfw_mode:
            await switch_model(ModelSwitchRequest(nsfw_mode=True, nsfw_model=variation_request.nsfw_model))
        elif CURRENT_NSFW_MODE:
            await switch_model(ModelSwitchRequest(nsfw_mode=False))

        if not img2img_pipe:
            await asyncio.to_thread(ensure_image_models_loaded)

        # Read uploaded image
        contents = await file.read()
        try:
            image = Image.open(io.BytesIO(contents)).convert("RGB")
        except Exception:
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")
        image = prepare_variation_image(image)

        prompt = " ".join((variation_request.prompt or "a beautiful high quality image").strip().split())
        if not prompt:
            prompt = "a beautiful high quality image"

        def generate():
            generator = make_generator(int(datetime.now().timestamp() * 1000) % (2**31))

            images = []
            with torch.inference_mode():
                for _ in range(variation_request.num_images):
                    output = img2img_pipe(
                        prompt=prompt,
                        negative_prompt=variation_request.negative_prompt or None,
                        image=image,
                        strength=variation_request.strength,
                        num_inference_steps=variation_request.num_inference_steps,
                        guidance_scale=variation_request.guidance_scale,
                        generator=generator,
                    )
                    images.append(output.images[0])

            return images

        images = await asyncio.to_thread(generate)

        results = []
        for new_image in images:
            filename = f"{uuid.uuid4()}.png"
            filepath = GALLERY_DIR / filename
            new_image.save(filepath)
            results.append({
                "id": filename.replace(".png", ""),
                "url": f"/image/{filename}",
                "filename": filename,
                "prompt": prompt,
            })

        response = {"success": True, "images": results, "total": len(results)}
        if results:
            response.update(results[0])
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/image/{filename}")
async def get_image(filename: str):
    """Retrieve a generated image"""
    filepath = GALLERY_DIR / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(filepath, media_type="image/png")

@app.get("/video/{filename}")
async def get_video(filename: str):
    """Retrieve a generated video."""
    filepath = GALLERY_DIR / filename

    if filepath.suffix.lower() != ".mp4" or not filepath.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(filepath, media_type="video/mp4")

@app.get("/gallery")
async def list_gallery():
    """List all generated images and videos."""
    media = []
    files = list(GALLERY_DIR.glob("*.png")) + list(GALLERY_DIR.glob("*.mp4"))
    for file in sorted(files, key=os.path.getmtime, reverse=True):
        media_type = "video" if file.suffix.lower() == ".mp4" else "image"
        media.append({
            "id": file.stem,
            "filename": file.name,
            "url": f"/{media_type}/{file.name}",
            "type": media_type,
            "created": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
        })
    
    return {"images": media, "total": len(media)}

@app.delete("/image/{filename}")
async def delete_image(filename: str):
    """Delete an image or video from gallery."""
    filepath = GALLERY_DIR / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Media not found")
    
    filepath.unlink()
    return {"success": True, "deleted": filename}

@app.delete("/gallery")
async def clear_gallery():
    """Clear all images and videos from gallery."""
    count = 0
    for file in list(GALLERY_DIR.glob("*.png")) + list(GALLERY_DIR.glob("*.mp4")):
        file.unlink()
        count += 1
    
    return {"success": True, "deleted": count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
