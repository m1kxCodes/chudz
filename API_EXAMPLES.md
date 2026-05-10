# Example API Calls - NoFilters Image Generator

This file demonstrates how to use the API directly with curl commands.

## Prerequisites

Make sure the server is running:
```
python backend/main.py
```

## Examples

### 1. Generate Single Image

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a beautiful purple sunset over mountains with stars",
    "negative_prompt": "ugly, distorted, low quality",
    "num_inference_steps": 50,
    "guidance_scale": 7.5,
    "height": 512,
    "width": 512,
    "num_images": 1
  }'
```

### 2. Generate Batch (Multiple Images)

```bash
curl -X POST "http://localhost:8000/generate-batch" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "cyberpunk city at night with neon lights",
    "negative_prompt": "blurry, low res",
    "num_inference_steps": 50,
    "guidance_scale": 7.5,
    "height": 512,
    "width": 512,
    "num_images": 4
  }'
```

### 3. Generate Video

```bash
curl -X POST "http://localhost:8000/generate-video" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a cinematic tracking shot of neon rain falling on a quiet city street",
    "negative_prompt": "blurry, low quality, flickering, text, watermark",
    "num_inference_steps": 25,
    "guidance_scale": 9,
    "width": 576,
    "height": 320,
    "num_frames": 16,
    "fps": 8
  }'
```

### 4. Create Image Variation

```bash
# First, prepare an image file (e.g., generated.png)
curl -X POST "http://localhost:8000/variation" \
  -F "file=@path/to/your/image.png"
```

### 5. Get Gallery

```bash
curl "http://localhost:8000/gallery"
```

Returns:
```json
{
  "images": [
    {
      "id": "abc123",
      "filename": "abc123.png",
      "url": "/image/abc123.png",
      "type": "image",
      "created": "2024-01-15T10:30:45.123456"
    }
  ],
  "total": 1
}
```

### 6. Get Specific Image

```bash
curl "http://localhost:8000/image/abc123.png" -o my_image.png
```

Or open in browser:
```
http://localhost:8000/image/abc123.png
```

### 7. Get Specific Video

```bash
curl "http://localhost:8000/video/abc123.mp4" -o my_video.mp4
```

### 8. Delete Media

```bash
curl -X DELETE "http://localhost:8000/image/abc123.png"
```

### 9. Clear Gallery

```bash
curl -X DELETE "http://localhost:8000/gallery"
```

### 8. Get Server Status

```bash
curl "http://localhost:8000/status"
```

Returns:
```json
{
  "device": "cuda",
  "gpu_available": true,
  "gpu_name": "NVIDIA GeForce RTX 3090"
}
```

## Python Examples

### Generate Image with Python

```python
import requests
import json

API_URL = "http://localhost:8000"

# Generate image
response = requests.post(f"{API_URL}/generate", json={
    "prompt": "a futuristic robot warrior",
    "negative_prompt": "ugly, distorted",
    "num_inference_steps": 50,
    "guidance_scale": 7.5,
    "height": 512,
    "width": 512,
    "num_images": 1
})

data = response.json()
print(f"Generated {len(data['images'])} images")

for img in data['images']:
    print(f"Download: {API_URL}{img['url']}")
```

### Download Images

```python
import requests
from pathlib import Path

API_URL = "http://localhost:8000"

# Get gallery
response = requests.get(f"{API_URL}/gallery")
images = response.json()["images"]

# Download all images
for img in images:
    url = f"{API_URL}{img['url']}"
    response = requests.get(url)
    
    Path("downloads").mkdir(exist_ok=True)
    with open(f"downloads/{img['filename']}", "wb") as f:
        f.write(response.content)
    print(f"Downloaded: {img['filename']}")
```

### Batch Generation

```python
import requests
import time

API_URL = "http://localhost:8000"

# Generate 5 variations of same prompt
response = requests.post(f"{API_URL}/generate-batch", json={
    "prompt": "a majestic phoenix rising from fire",
    "num_images": 5,
    "num_inference_steps": 50,
    "guidance_scale": 7.5,
    "height": 512,
    "width": 512
})

images = response.json()["images"]
print(f"Generated {len(images)} images!")
```

## JavaScript/Fetch Examples

### Generate Image with JavaScript

```javascript
const API_URL = 'http://localhost:8000';

async function generateImage(prompt) {
    const response = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            prompt: prompt,
            negative_prompt: "ugly, distorted",
            num_inference_steps: 50,
            guidance_scale: 7.5,
            height: 512,
            width: 512,
            num_images: 1
        })
    });

    const data = await response.json();
    console.log('Generated images:', data.images);
    return data.images;
}

// Usage
generateImage("a beautiful landscape");
```

### Load Gallery in JavaScript

```javascript
async function loadGallery() {
    const response = await fetch('http://localhost:8000/gallery');
    const data = await response.json();
    
    console.log(`Loaded ${data.total} images`);
    data.images.forEach(img => {
        console.log(`${img.filename}: ${img.url}`);
    });
}

loadGallery();
```

## Prompt Engineering Tips

### Good Prompts
- Specific and detailed
- Include style, mood, lighting
- Use adjectives and descriptive words

Examples:
```
"a hyperrealistic portrait of a cyborg warrior, cyberpunk style, neon lights, highly detailed, 4k"
"a steampunk airship flying over victorian city, sunset lighting, dramatic clouds, digital art"
"underwater alien civilization, bioluminescent creatures, coral architecture, cinematic lighting"
```

### Negative Prompts
Used to exclude unwanted elements:
```
"ugly, distorted, low quality, blurry, watermark, text, deformed"
"bad anatomy, bad proportions, poorly rendered"
```

## Performance Tuning

### For Faster Generation
```json
{
    "prompt": "your prompt",
    "num_inference_steps": 20,    // Lower steps = faster
    "height": 256,                 // Smaller size = faster
    "width": 256,
    "guidance_scale": 5.0          // Lower guidance = faster
}
```

### For Better Quality
```json
{
    "prompt": "your prompt",
    "num_inference_steps": 100,    // Higher steps = better
    "height": 768,                 // Larger size = better
    "width": 768,
    "guidance_scale": 15.0         // Higher guidance = better
}
```

## Troubleshooting

### CORS Issues
If you get CORS errors, the API is already configured with CORS enabled.
Make sure you're accessing from the same machine or add to firewall.

### File Size Issues
Images are saved as PNG (larger files). To reduce:
- Use smaller dimensions (256x256 vs 512x512)
- Consider converting to JPG after generation

### Memory Issues
```json
{
    "prompt": "your prompt",
    "height": 256,    // Reduce dimensions
    "width": 256,
    "num_inference_steps": 20     // Reduce steps
}
```

---

For full API documentation, visit: `http://localhost:8000/docs`
