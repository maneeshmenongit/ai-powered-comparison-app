#!/usr/bin/env python3
"""
Optimize trips sticker for empty state
"""
from PIL import Image
import os

input_path = 'frontend/assets/stickers/trips_sticker.png'
output_path = 'frontend/assets/images/trips_empty_icon.png'

print(f"Processing: {input_path}")

# Open image
img = Image.open(input_path)
print(f"Original size: {img.size}, Mode: {img.mode}")

# Convert to RGBA if not already
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# Resize to appropriate size for empty state (150px - larger for visual impact)
max_size = 150
aspect_ratio = img.width / img.height

if img.width > img.height:
    new_width = max_size
    new_height = int(max_size / aspect_ratio)
else:
    new_height = max_size
    new_width = int(max_size * aspect_ratio)

img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
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
