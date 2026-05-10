# Feature Guide - NoFilters Image Generator

Complete guide to all features and how to use them.

## 🎨 Main Features

### 1. Text to Image Generation

**What it does**: Generate images from text descriptions

**How to use**:
1. Go to "Generate" tab
2. Enter your prompt (describe what you want)
3. Adjust settings if desired
4. Click "Generate Image"
5. Wait 20-60 seconds
6. Download or delete

**Tips**:
- Be specific: "a purple mountain at sunset" vs "mountain"
- Include style: "oil painting", "digital art", "photorealistic"
- Add mood: "dramatic", "peaceful", "chaotic"
- Use adjectives: "beautiful", "detailed", "intricate"

**Example prompts**:
```
"A majestic dragon breathing fire, fantasy art style, dramatic lighting"
"Steampunk airship over Victorian city, sunset, atmospheric"
"Bioluminescent alien forest, otherworldly, cinematic lighting"
```

### 2. Batch Generation

**What it does**: Generate multiple images with the same prompt, each with different variations

**How to use**:
1. Go to "Batch" tab
2. Enter prompt
3. Set "Number of Images" (1-10)
4. Click "Generate Batch"
5. Wait while multiple images are generated
6. All images appear together

**Benefits**:
- Explore different interpretations
- Find the best variation
- Takes roughly the same time as generating 1 image but gives you options

**Example**:
```
Prompt: "cyberpunk warrior with glowing sword"
Number of images: 4
Result: 4 different interpretations
```

### 3. Image Variations

**What it does**: Take an existing image and create a variation of it

**How to use**:
1. Go to "Variation" tab
2. Click file input and select an image
3. Preview shows your image
4. Click "Create Variation"
5. New variation appears below

**Use cases**:
- Tweak generated images you almost like
- Create alternatives to existing images
- Explore different styles of same subject
- Refine designs

### 4. Gallery Management

**What it does**: View, download, and manage all generated images

**How to use**:
1. Go to "Gallery" tab
2. View all your generated images in a grid
3. Hover over images to see options
4. Download: Save image to your computer
5. Delete: Remove from gallery
6. "Clear All" button removes everything

**Features**:
- Automatic sorting (newest first)
- Shows creation time
- One-click download
- Batch delete capability

## ⚙️ Generation Settings Explained

### Steps (Inference Steps)
- **Range**: 1-150
- **Default**: 50
- **Effect**: How many times the AI refines the image
- **Quality**: More steps = better quality but slower
- **Recommendation**: 
  - Fast: 20-30 steps
  - Balanced: 40-60 steps
  - High quality: 75-100 steps

### Guidance Scale
- **Range**: 1-20
- **Default**: 7.5
- **Effect**: How strictly the AI follows your prompt
- **Lower values**: More creative but less accurate
- **Higher values**: Very faithful to prompt but less creative
- **Recommendation**:
  - Loose: 3-5
  - Balanced: 6-10
  - Strict: 11-15

### Image Dimensions
- **Options**: 256×256, 384×384, 512×512, 640×640, 768×768
- **Default**: 512×512
- **Speed**: Smaller = faster
- **Quality**: Larger = better detail
- **Memory**: Larger needs more GPU memory
- **Recommendation**:
  - Fast: 256×256
  - Balanced: 512×512
  - High quality: 768×768

### Negative Prompt
- **What it is**: Things to AVOID in the image
- **Example**: "ugly, distorted, low quality, watermark"
- **Purpose**: Removes unwanted elements
- **Common values**:
  - "ugly, distorted, blurry, low quality"
  - "bad anatomy, bad proportions, deformed"
  - "watermark, text, signature"

## 🎯 Advanced Tips

### Better Prompt Engineering

**Weak prompt**:
```
"a cat"
```

**Strong prompt**:
```
"a majestic fluffy tabby cat with green eyes, sitting on a velvet chair, 
soft warm lighting, detailed fur, photorealistic, 4k, professional photography"
```

**Formula for good prompts**:
1. Main subject: "a warrior"
2. Descriptors: "fierce, muscular"
3. Environment: "in a dark castle"
4. Style: "oil painting, fantasy art"
5. Quality hints: "detailed, 4k, professional"
6. Lighting: "dramatic lighting, shadows"

### Negative Prompt Examples

**For photorealistic images**:
```
"painting, drawing, illustration, abstract, cartoon, low quality, blurry"
```

**For fantasy art**:
```
"photorealistic, realistic, photo, photograph, modern, contemporary"
```

**General safe list**:
```
"ugly, distorted, deformed, bad quality, blurry, watermark, text, signature"
```

### Style Keywords

Insert any of these into your prompt:

**Art Styles**:
- oil painting, watercolor, digital art, concept art, illustration
- anime, manga, cartoon, comic, pixel art
- photorealistic, hyper-realistic, realistic, fantasy art

**Quality Enhancers**:
- 4k, 8k, detailed, intricate, fine details, sharp focus
- trending on artstation, professional, award-winning
- cinematic, dramatic, atmospheric, moody

**Lighting Types**:
- volumetric lighting, studio lighting, golden hour
- neon lights, backlighting, rim lighting, shadows
- dramatic lighting, soft lighting, natural lighting

**Camera Terms**:
- close-up, wide shot, panoramic, overhead view
- depth of field, shallow focus, ultra wide angle

## 📊 Performance Optimization

### For Maximum Speed
```
Steps: 20
Guidance: 5.0
Size: 256×256
Negative: "ugly"
Result: ~5 seconds with GPU, ~30 seconds with CPU
```

### For Maximum Quality
```
Steps: 100
Guidance: 12.0
Size: 768×768
Negative: "ugly, distorted, blurry, low quality"
Result: ~30 seconds with GPU, ~5 minutes with CPU
```

### Balanced (Recommended)
```
Steps: 50
Guidance: 7.5
Size: 512×512
Negative: "ugly, distorted, blurry"
Result: ~15 seconds with GPU, ~2 minutes with CPU
```

## 🔧 Troubleshooting Features

### Image quality is poor
- ✓ Increase steps (50 → 75-100)
- ✓ Better prompt (add more details)
- ✓ Use negative prompt
- ✓ Try higher guidance scale (7.5 → 10)

### Generation is too slow
- ✓ Reduce steps (50 → 20-30)
- ✓ Reduce image size (512 → 256)
- ✓ Reduce guidance scale (7.5 → 5)
- ✓ Install current GPU drivers (AMD DirectML or NVIDIA CUDA)

### Server is running slowly
- ✓ Close other applications
- ✓ Free up disk space
- ✓ Reduce number of simultaneous requests
- ✓ Restart the server

### Images look the same
- ✓ Use different prompts (not just different words)
- ✓ Use batch generation with different prompts
- ✓ Try different guidance values
- ✓ Use variation feature on existing images

## 🎬 Using the API Directly

See [API_EXAMPLES.md](API_EXAMPLES.md) for:
- cURL commands
- Python examples
- JavaScript examples
- Batch processing
- Advanced automation

## 📱 Keyboard Shortcuts

- **Tab Navigation**: Tab key moves between form fields
- **Generate**: Tab to button and press Enter
- **Reset Gallery**: Refresh page to reload

## 💾 File Management

### Where images are stored
- All generated images: `gallery/` folder
- Images named by: UUID (unique identifier)
- Format: PNG (lossless, larger files)
- Size: ~500KB - 2MB per image

### Downloading images
- Gallery tab: Click "Download" button
- Browser default folder: Usually Downloads
- Or save-as in context menu

### Deleting images
- Gallery tab: Hover and click "Delete"
- Or "Clear All" to remove everything
- Deleted images free up disk space

## 🎪 Fun Experiments

### Style Transfer
Generate both real and artistic versions:
```
1. "A photo of a sunset"
2. "A painting of the same sunset in Van Gogh style"
Compare them!
```

### Character Consistency
Generate character from different angles:
```
1. "A wizard front view, full body, fantasy"
2. "A wizard side view, full body, fantasy"  (may differ due to random seed)
3. Use variation feature to create consistent variations
```

### Prompt Variations
Test how words affect output:
```
1. "A castle"
2. "An ancient castle"
3. "A beautiful ancient castle"
4. "A mysterious ancient castle on a mountain"
See how adding details improves results
```

## 🚀 Getting the Best Results

1. **Start simple**: Test basic prompts first
2. **Build up**: Add modifiers gradually
3. **Use examples**: Reference art styles you like
4. **Iterate**: Use variations to refine
5. **Experiment**: Try different settings
6. **Learn**: Save what works and note it

## Summary of All Features

| Feature | Tab | Purpose | Time |
|---------|-----|---------|------|
| Text to Image | Generate | Create single image from prompt | 20-60s |
| Batch Generation | Batch | Create 2-10 variations | 40-600s |
| Image Variation | Variation | Create variation of uploaded image | 20-60s |
| Gallery View | Gallery | View/download/delete all images | Instant |
| API Access | - | Automate via HTTP requests | Custom |

---

**Ready to create amazing images? Let's go! 🎨**
