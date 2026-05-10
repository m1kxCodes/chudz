# 🎨 NoFilters Image Generator

An AI image generator with **no content restrictions** - generate unlimited creative images using Stable Diffusion v1.5.

## Features

✨ **Text to Image** - Generate images from text prompts  
🎬 **Text to Video** - Generate short MP4 clips from text prompts  
🔄 **Batch Generation** - Create multiple variations at once  
🎭 **Image Variations** - Create variations of existing images  
📸 **Gallery** - View, download, and manage all generated images  
⚡ **GPU Accelerated** - CUDA and DirectML support with CPU fallback  
🖥️ **Web Interface** - Beautiful, responsive UI  
🔓 **No Filters** - No content moderation, generate anything  

## System Requirements

- **Python 3.9+**
- **GPU** (highly recommended - 6GB+ VRAM for smooth performance)
  - NVIDIA GPUs can use CUDA
  - AMD GPUs can use DirectML on Windows
  - Falls back to CPU mode if GPU unavailable
- **Windows 10+** (or Linux/macOS with Python)

## Installation

### 1. Clone or Download

```bash
cd NoFiltersImageGen
```

### 2. Create Python Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

`requirements.txt` is the DirectML default. For NVIDIA CUDA instead, run:

```bash
pip install -r requirements-cuda.txt
```

**Note:** First installation may take 10-15 minutes as it downloads the Stable Diffusion model (~4GB).

### 4. Create Gallery Directory

The gallery directory already exists but can be manually created:

```bash
# From project root
mkdir gallery
```

## Usage

### Start the Backend Server

```bash
cd backend
python main.py
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The models will load on first startup (this takes 1-2 minutes). Progress will be shown in the terminal.

### Open the Frontend

1. Open your web browser
2. Navigate to: `http://localhost:8000/docs` (API documentation)
3. Or use the web interface - open `frontend/index.html` in your browser

### Features Overview

#### Generate
- Enter a text prompt describing what you want
- Adjust steps (quality), guidance scale (adherence to prompt), and dimensions
- Click "Generate Image"
- Download or delete the result

#### Batch
- Generate multiple variations of the same prompt at once
- Each variation uses a different random seed
- Perfect for exploring different interpretations

#### Variations
- Upload an existing image
- The AI creates a new variation based on it
- Useful for tweaking designs

#### Gallery
- View all previously generated images
- Download individual images
- Clear all images at once

## Configuration

Edit `backend/main.py` to customize:

```python
MODEL_ID = "runwayml/stable-diffusion-v1-5"  # Model to use
device = auto  # In config.ini: CUDA if available, then DirectML, then CPU
```

### Available Models

- `runwayml/stable-diffusion-v1-5` - Base model (default)
- `runwayml/stable-diffusion-v2-1-base` - V2.1 (may require more VRAM)
- Custom Hugging Face models supported

## API Endpoints

### Generation
```bash
POST /generate
- prompt: string
- negative_prompt: string (optional)
- num_inference_steps: int (1-150, default: 50)
- guidance_scale: float (1-20, default: 7.5)
- height: int (256-768, default: 512)
- width: int (256-768, default: 512)
- num_images: int (1-10, default: 1)

Returns: { success: true, images: [...] }
```

### Batch Generation
```bash
POST /generate-batch
Same parameters as /generate
```

### Video Generation
```bash
POST /generate-video
- prompt: string
- negative_prompt: string (optional)
- num_inference_steps: int (default: 25)
- guidance_scale: float (default: 9.0)
- width: int (default: 576)
- height: int (default: 320)
- num_frames: int (default: 16)
- fps: int (default: 8)
Returns: { success: true, video: {...} }
```

### Image Variations
```bash
POST /variation
- file: Image file (multipart/form-data)

Returns: { success: true, id, url, filename }
```

### Gallery
```bash
GET /gallery
Returns: { images: [...], total: int }

DELETE /gallery
Clears all images

GET /image/{filename}
Download specific image

GET /video/{filename}
Download specific video

DELETE /image/{filename}
Delete specific image or video
```

## Performance Tips

### Speed up generation
1. **Use GPU** - Install the dependency profile for your GPU backend
2. **Reduce steps** - Lower values (20-30) for faster generation, higher for quality (50-100)
3. **Use smaller dimensions** - 512x512 is default, use 256x256 for speed
4. **Reduce guidance scale** - Lower values (3-5) generate faster

### Improve quality
1. **Increase steps** - 50-100 steps for good quality
2. **Increase guidance scale** - 7.5-12 for better prompt adherence
3. **Better prompts** - Specific, detailed prompts yield better results
4. **Use negative prompts** - Specify what NOT to include

## Troubleshooting

### "Out of Memory" Error
```
RuntimeError: CUDA/DirectML out of memory
```
Solution:
- Reduce image dimensions (512x512 → 256x256)
- Reduce number of inference steps
- Use CPU mode instead (slower but works)
- Restart the server

### Models won't download
```
huggingface_hub.utils._errors.RepositoryNotFound
```
Solution:
- Check internet connection
- Verify Hugging Face is accessible
- Try using a different model ID
- Clear cache: `rm -rf ~/.cache/huggingface/`

### Port 8000 already in use
```
OSError: [Errno 48] Address already in use
```
Solution:
- Kill existing process: `lsof -ti:8000 | xargs kill -9`
- Or change port in `main.py`: `uvicorn.run(app, port=8001)`

### Browser can't connect to API
- Ensure backend is running on http://localhost:8000
- Check firewall settings
- Verify no proxy interfering
- Try clearing browser cache

## Environment Variables

Optional configuration via environment variables:

```bash
# Override device selection
NOFILTERS_DEVICE=auto

# Hugging Face token (for private models)
HUGGINGFACE_API_KEY=hf_...

# Custom gallery path
GALLERY_PATH=/path/to/gallery
```

## Model Information

**Stable Diffusion v1.5**
- Base model: 862M parameters
- Download size: ~4GB
- Memory required: 3-6GB VRAM (GPU) or 8GB+ RAM (CPU)
- Speed: ~20-60 seconds per image (GPU), ~5-10 minutes (CPU)
- License: OpenRAI License (free for commercial and non-commercial use)

## Security Notes

⚠️ **No Content Filter** - This tool generates images without content filtering
- Generated images are stored in the `gallery` directory
- Only run on personal machines or trusted networks
- Consider privacy and local laws when generating images
- API has no authentication - do not expose to untrusted networks

## Advanced Usage

### Running with custom settings

```python
# In config.ini
device = cpu       # Force CPU mode
# or
device = amd       # Force AMD GPU mode on Windows
# or
device = cuda      # Force NVIDIA CUDA mode
```

### Using different models

```python
MODEL_ID = "runwayml/stable-diffusion-v2-1-base"
# or any Hugging Face diffusers model
```

### Batch processing via API

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a beautiful sunset",
    "num_images": 4,
    "num_inference_steps": 50
  }'
```

## Performance Benchmarks

**NVIDIA RTX 3090 (24GB VRAM)**
- 512x512, 50 steps: ~8 seconds
- 512x512, 100 steps: ~15 seconds
- Batch of 4 images: ~25 seconds

**NVIDIA RTX 2060 (6GB VRAM)**
- 512x512, 20 steps: ~30 seconds
- 256x256, 50 steps: ~15 seconds

**CPU (Intel i7, 16GB RAM)**
- 512x512, 20 steps: ~3 minutes
- 256x256, 20 steps: ~1.5 minutes

## File Structure

```
NoFiltersImageGen/
├── backend/
│   ├── main.py              # FastAPI application
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── index.html           # Web UI
│   ├── styles.css           # Styling
│   └── script.js            # Frontend logic
├── gallery/                 # Generated images stored here
└── README.md               # This file
```

## Contributing

Found a bug or have suggestions? Feel free to improve the code!

## License

This project uses Stable Diffusion under the OpenRAI License.
Frontend and backend code are provided as-is for personal use.

## Disclaimer

- Images are generated by AI and may not be perfect
- First generation takes longer as models load
- Some GPU memory required - CPU fallback is very slow
- Generated images are stored locally in the `gallery` directory
- Use responsibly and in compliance with local laws

---

**Enjoy unlimited creative image generation! 🚀**
