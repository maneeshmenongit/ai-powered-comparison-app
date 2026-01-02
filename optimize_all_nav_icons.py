#!/usr/bin/env python3
"""
Batch optimize all navigation icons
"""
from PIL import Image
import os

# Icons to process
icons = {
    'search': 'search_icon_original.png',
    'ride': 'ride_icon_original.png',
    'favorite': 'favorite_icon_original.png',
    'profile': 'profile_icon_original.png'
}

base_path = 'frontend/assets/images'
max_size = 64  # Max dimension in pixels
threshold = 240  # White background threshold

print("=" * 60)
print("OPTIMIZING NAVIGATION ICONS")
print("=" * 60)

for icon_name, original_file in icons.items():
    input_path = os.path.join(base_path, original_file)
    output_path = os.path.join(base_path, f'{icon_name}_icon.png')

    if not os.path.exists(input_path):
        print(f"\n❌ {icon_name}: {original_file} not found, skipping")
        continue

    print(f"\n📦 Processing: {icon_name}_icon")
    print(f"   Input: {original_file}")

    # Open image
    img = Image.open(input_path)
    original_size = img.size
    original_mode = img.mode

    # Convert to RGBA
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Remove white background
    datas = img.getdata()
    new_data = []

    for item in datas:
        # Check if pixel is white or near-white
        if item[0] > threshold and item[1] > threshold and item[2] > threshold:
            new_data.append((255, 255, 255, 0))  # Transparent
        else:
            new_data.append(item)

    img.putdata(new_data)

    # Crop to content
    bbox = img.getbbox()

    if bbox:
        img_cropped = img.crop(bbox)

        # Resize maintaining aspect ratio
        aspect_ratio = img_cropped.width / img_cropped.height

        if img_cropped.width > img_cropped.height:
            new_width = max_size
            new_height = int(max_size / aspect_ratio)
        else:
            new_height = max_size
            new_width = int(max_size * aspect_ratio)

        img_resized = img_cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Save optimized version
        img_resized.save(output_path, 'PNG', optimize=True)

        # Get file sizes
        input_size_kb = os.path.getsize(input_path) / 1024
        output_size_kb = os.path.getsize(output_path) / 1024
        reduction = ((input_size_kb - output_size_kb) / input_size_kb) * 100

        print(f"   ✅ Original: {original_size[0]}x{original_size[1]} ({input_size_kb:.1f}KB)")
        print(f"   ✅ Optimized: {img_resized.size[0]}x{img_resized.size[1]} ({output_size_kb:.1f}KB)")
        print(f"   ✅ Reduction: {reduction:.1f}%")
    else:
        print(f"   ❌ Could not find content to crop")

print("\n" + "=" * 60)
print("OPTIMIZATION COMPLETE!")
print("=" * 60)
print("\nGenerated files:")
for icon_name in icons.keys():
    output_path = os.path.join(base_path, f'{icon_name}_icon.png')
    if os.path.exists(output_path):
        size = os.path.getsize(output_path) / 1024
        img = Image.open(output_path)
        print(f"  ✅ {icon_name}_icon.png - {img.size[0]}x{img.size[1]} ({size:.1f}KB)")
