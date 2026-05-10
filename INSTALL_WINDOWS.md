# Installation Guide for Windows

Complete step-by-step guide to set up NoFilters Image Generator on Windows.

## Prerequisites

### System Requirements
- **Windows 10 or Windows 11**
- **Python 3.9 or higher**
- **15GB+ free disk space** (for models)
- **8GB+ RAM** (16GB+ recommended)
- **NVIDIA GPU (optional but recommended)**

### Step 1: Install Python

1. Download Python from https://www.python.org/downloads/
2. Run the installer
3. **Important**: Check "Add Python to PATH"
4. Click "Install Now"
5. Verify installation:
   ```
   Open PowerShell and run: python --version
   ```
   Should show: `Python 3.9.x` or higher

### Step 2: Download Project

You already have the project in:
```
C:\Users\misss\Downloads\NoFiltersImageGen
```

Or download from repository if needed.

## Installation

### Option A: Easy Installation (Recommended)

1. **Double-click `start.bat`** in the project folder
2. Wait for installation to complete (first time takes 5-10 minutes)
3. You'll see: `Uvicorn running on http://0.0.0.0:8000`
4. The terminal will stay open - this is normal
5. Open browser: `file:///C:/Users/misss/Downloads/NoFiltersImageGen/frontend/index.html`

Or open the launcher: `launch.html`

### Option B: Manual Installation

1. **Open PowerShell** in the project folder
2. **Create virtual environment:**
   ```powershell
   python -m venv venv
   ```
3. **Activate it:**
   ```powershell
   venv\Scripts\activate
   ```
   You should see `(venv)` at the start of the line

4. **Install dependencies:**
   ```powershell
   cd backend
   pip install -r requirements.txt
   ```
   This downloads models (~4GB) - takes 10-15 minutes on first run

5. **Start the server:**
   ```powershell
   python main.py
   ```
   Wait until you see: `Uvicorn running on http://0.0.0.0:8000`

6. **In another PowerShell window, open the frontend:**
   ```powershell
   # Navigate to project folder
   cd NoFiltersImageGen
   # Open in default browser
   start frontend/index.html
   ```

## First Use

### Wait for Model Loading
- First generation will take 1-2 minutes
- Models are downloading and compiling
- Watch the PowerShell terminal for progress
- Subsequent generations are much faster (20-60 seconds)

### Test Generation
1. Go to "Generate" tab
2. Enter prompt: `a beautiful sunset`
3. Click "Generate Image"
4. Wait for result

## GPU Setup (Optional - Recommended)

For much faster generation (10x faster), install NVIDIA CUDA:

### Check if you have NVIDIA GPU
1. Right-click on desktop
2. Look for "NVIDIA Control Panel" option
3. If present, you have an NVIDIA GPU

### Install CUDA Toolkit

1. Download CUDA 11.8 from: https://developer.nvidia.com/cuda-11-8-0-download-archive
2. Run installer and follow prompts
3. Install cuDNN (required for best performance):
   - Download from: https://developer.nvidia.com/cudnn
   - Extract to CUDA installation folder
4. Reinstall PyTorch:
   ```powershell
   cd backend
   pip install torch torchvision --force-reinstall
   ```

### Verify GPU is working
1. Start server as usual
2. Check terminal output - should say "cuda" instead of "cpu"
3. In web interface, check top right for GPU info

## Troubleshooting

### "Python is not recognized"
**Solution**: Python not in PATH
- Reinstall Python
- Make sure to check "Add Python to PATH"
- Restart PowerShell after installation

### "ModuleNotFoundError: No module named 'torch'"
**Solution**: Dependencies not installed
```powershell
cd backend
pip install -r requirements.txt --force-reinstall
```

### "CUDA out of memory" error
**Solution**: Reduce settings
- Lower image size: 512 → 256
- Lower steps: 50 → 20
- Restart server
- Close other programs using GPU

### "Address already in use" error
**Solution**: Port 8000 is taken
```powershell
# Kill process using port 8000
Get-Process | Where-Object {$_.Handles -like "*8000*"} | Stop-Process -Force

# Or edit backend/main.py and change port to 8001
```

### "Connection refused" in browser
**Checklist:**
- ✓ PowerShell terminal is still open and running
- ✓ Server shows "Uvicorn running"
- ✓ Firewall not blocking port 8000
- ✓ Try different browser (Chrome, Firefox, Edge)

### Models won't download
**Solution:**
```powershell
# Clear cache
rm -r $env:USERPROFILE\.cache\huggingface

# Try again
python main.py
```

### "Out of disk space" error
**Solution**: You need at least 15GB free
- Models take ~4GB
- Generated images use additional space
- Clear old images from gallery folder

## Updating

To update to latest dependencies:

```powershell
cd backend
pip install -r requirements.txt --upgrade
```

## Uninstalling

Just delete the folder:
```powershell
Remove-Item -Recurse C:\Users\misss\Downloads\NoFiltersImageGen
```

Or through File Explorer, right-click folder → Delete

## Performance Tips

### Faster Generation
- Use GPU (see GPU Setup section)
- Reduce steps: 20-30 (faster, lower quality)
- Smaller image size: 256x256 instead of 512x512
- Close other applications

### Better Quality
- More steps: 75-100
- Larger size: 768x768
- Better prompts (specific, detailed)
- Use negative prompts to avoid artifacts

## Advanced Configuration

Edit `config.ini` to customize:

```ini
[MODEL]
# Change which Stable Diffusion model to use
model_id = runwayml/stable-diffusion-v1-5

[GENERATION]
# Default values
default_steps = 50
default_guidance_scale = 7.5
```

Or edit `backend/main.py` for more options.

## Next Steps

1. Try different prompts
2. Read [API_EXAMPLES.md](API_EXAMPLES.md) for advanced usage
3. Check [README.md](README.md) for full documentation
4. Visit API docs: http://localhost:8000/docs

## Getting Help

**Server won't start?**
- Check Python version: `python --version`
- Check disk space: `dir C:\Users\misss\Downloads\NoFiltersImageGen`
- Check internet connection (for model download)

**Generation too slow?**
- Try GPU setup (instructions above)
- Reduce image size and steps
- Check that no other applications are using GPU

**Images look bad?**
- Write better prompts
- Use higher step counts
- Check GPU has enough VRAM

## Summary

1. ✅ Run `start.bat`
2. ✅ Wait for model load (1-2 minutes)
3. ✅ Open `launch.html` or `frontend/index.html`
4. ✅ Generate amazing images!

---

**Happy generating! 🚀**
