#!/usr/bin/env python3
"""
Optimize home icon by removing white background and cropping to content
"""
from PIL import Image
import os

# Paths
input_path = 'frontend/assets/images/home_icon.png'
output_path = 'frontend/assets/images/home_icon.png'
backup_path = 'frontend/assets/images/home_icon_original_v2.png'

print(f"Processing: {input_path}")

# Open image
img = Image.open(input_path)
print(f"Original size: {img.size}, Mode: {img.mode}")

# Backup original
img.save(backup_path)
print(f"✅ Backup saved to: {backup_path}")

# Convert to RGBA if not already
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# Get image data
datas = img.getdata()

# Replace white/near-white with transparent
new_data = []
threshold = 240  # Pixels brighter than this become transparent

for item in datas:
    # Check if pixel is white or near-white
    if item[0] > threshold and item[1] > threshold and item[2] > threshold:
        # Make it transparent
        new_data.append((255, 255, 255, 0))
    else:
        new_data.append(item)

img.putdata(new_data)
print("✅ White background removed")

# Get bounding box of non-transparent pixels
bbox = img.getbbox()

if bbox:
    # Crop to content
    img_cropped = img.crop(bbox)
    print(f"✅ Cropped from {img.size} to {img_cropped.size}")

    # Resize to reasonable size for nav icon (max 64px height)
    max_height = 64
    aspect_ratio = img_cropped.width / img_cropped.height
    new_height = max_height
    new_width = int(max_height * aspect_ratio)

    img_resized = img_cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)
    print(f"✅ Resized to: {img_resized.size}")

    # Save optimized version
    img_resized.save(output_path, 'PNG', optimize=True)

    # Check file size
    size_kb = os.path.getsize(output_path) / 1024
    print(f"✅ Saved optimized icon: {size_kb:.1f}KB")
    print(f"   Size: {img_resized.size[0]}x{img_resized.size[1]}")
else:
    print("❌ Could not find content to crop")
