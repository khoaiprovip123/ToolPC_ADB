"""
Convert PNG logo to ICO format for Windows app icon
"""
from PIL import Image
import os

# Load logo
logo_path = r"C:\Users\vankh\Downloads\Logo.png"
output_ico = "resources/icon.ico"

# Open image
img = Image.open(logo_path)

# Convert RGBA to RGB if needed (ICO doesn't support transparency well in all sizes)
if img.mode == 'RGBA':
    # Create white background
    background = Image.new('RGB', img.size, (255, 255, 255))
    background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
    img = background

# Create multiple sizes for ICO (Windows standard sizes)
sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
icon_images = []

for size in sizes:
    resized = img.resize(size, Image.Resampling.LANCZOS)
    icon_images.append(resized)

# Save as ICO
os.makedirs("resources", exist_ok=True)
icon_images[0].save(output_ico, format='ICO', sizes=[(s.width, s.height) for s in icon_images], append_images=icon_images[1:])

print(f"✅ Created icon: {output_ico}")
print(f"   Sizes: {', '.join([f'{s[0]}x{s[1]}' for s in sizes])}")
