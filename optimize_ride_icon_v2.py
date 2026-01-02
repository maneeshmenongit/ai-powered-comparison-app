#!/usr/bin/env python3
"""
Optimize ride icon v2 for Compare Rides section
"""
from PIL import Image
import os

input_path = 'frontend/assets/images/ride_icon_original_v2.png'
output_path = 'frontend/assets/images/ride_icon_large.png'

print(f"Processing: {input_path}")

# Open image
img = Image.open(input_path)
print(f"Original size: {img.size}, Mode: {img.mode}")

# Convert to RGBA if not already
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# Get image data
datas = img.getdata()

# Replace white/near-white with transparent
new_data = []
threshold = 240

for item in datas:
    if item[0] > threshold and item[1] > threshold and item[2] > threshold:
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

    # Resize to larger size for the Compare Rides button (128px)
    max_size = 128
    aspect_ratio = img_cropped.width / img_cropped.height

    if img_cropped.width > img_cropped.height:
        new_width = max_size
        new_height = int(max_size / aspect_ratio)
    else:
        new_height = max_size
        new_width = int(max_size * aspect_ratio)

    img_resized = img_cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)
    print(f"✅ Resized to: {img_resized.size}")

    # Save optimized version
    img_resized.save(output_path, 'PNG', optimize=True)

    # Check file size
    input_size_kb = os.path.getsize(input_path) / 1024
    output_size_kb = os.path.getsize(output_path) / 1024
    reduction = ((input_size_kb - output_size_kb) / input_size_kb) * 100

    print(f"✅ Saved: {output_path}")
    print(f"   Original: {input_size_kb:.1f}KB → Optimized: {output_size_kb:.1f}KB")
    print(f"   Reduction: {reduction:.1f}%")
else:
    print("❌ Could not find content to crop")
