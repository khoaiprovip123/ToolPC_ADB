from PIL import Image
import os

def create_ico():
    try:
        source = "resources/logo.png"
        dest = "resources/icon.ico"
        
        if not os.path.exists(source):
            print(f"Error: {source} not found")
            return
            
        img = Image.open(source)
        # Resize if necessary ? High res is fine for ICO containing multiple sizes
        # Just save as ICO
        img.save(dest, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
        print(f"Successfully created {dest}")
        
    except Exception as e:
        print(f"Error creating icon: {e}")

if __name__ == "__main__":
    create_ico()
