# Quick Start Guide - NoFilters Image Generator

## 5-Minute Setup

### Step 1: Prerequisites Check
Make sure you have:
- Python 3.9 or higher: `python --version`
- About 15GB free disk space (for models)
- 8GB+ RAM (more for GPU)

### Step 2: Install & Run

```bash
# Open PowerShell in the project folder

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Start server
python main.py
```

### Step 3: Use the App

1. **Open frontend**: Double-click `frontend/index.html`
   - Or navigate to it in any web browser

2. **First generation takes 1-2 minutes** (models loading)
   - Check terminal for progress

3. **Start generating!**
   - Enter a prompt like: "a beautiful purple sunset over mountains"
   - Click "Generate Image"
   - Wait 20-60 seconds
   - Download or delete images

## Troubleshooting

**Problem: "models not loaded yet"**
- Wait 2-3 minutes for initial model load
- Watch terminal for progress messages

**Problem: "CUDA out of memory"**
- Reduce image size (512 → 256)
- Reduce steps (50 → 20)
- Restart server
- Use CPU mode (slower but works)

**Problem: Can't open index.html**
- Right-click → Open with → Your browser
- Or copy this to address bar: `file:///C:/path/to/frontend/index.html`

## Pro Tips

- **Better prompts = Better images**
  - Good: "a futuristic cyberpunk city, neon lights, night"
  - Bad: "city"

- **Use negative prompts** to avoid unwanted elements
  - Example: "ugly, distorted, blurry"

- **Lower steps = faster** (20-30 steps)
- **Higher steps = better quality** (75-100 steps)

- **GPU mode is 10x faster** than CPU
  - If you have NVIDIA GPU, install CUDA toolkit

## Next Steps

- Read [README.md](README.md) for full documentation
- Experiment with different prompts
- Check API docs at http://localhost:8000/docs
- Adjust settings for your hardware

## Common Prompts to Try

- "A majestic dragon flying through clouds at sunset"
- "Steampunk airship over Victorian city"
- "Underwater alien civilization with glowing creatures"
- "Hyperrealistic portrait of a cyborg warrior"
- "Abstract colorful geometric patterns"

---

Happy generating! 🎨
