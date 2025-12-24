
import os
import subprocess
import sys

def find_iscc():
    possible_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Try finding in PATH
    try:
        result = subprocess.run(["where", "ISCC"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
    except:
        pass
        
    return None

def main():
    print("🚀 Looking for Inno Setup Compiler...")
    iscc_path = find_iscc()
    
    if not iscc_path:
        print("❌ Error: Inno Setup (ISCC.exe) not found!")
        print("Please install Inno Setup 6 from https://jrsoftware.org/isdl.php")
        sys.exit(1)
        
    print(f"✅ Found ISCC at: {iscc_path}")
    
    iss_file = os.path.abspath("installer.iss")
    if not os.path.exists(iss_file):
        print(f"❌ Error: {iss_file} not found!")
        sys.exit(1)
        
    print(f"📦 Compiling {iss_file}...")
    
    cmd = [iscc_path, iss_file]
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode == 0:
            print("\n✨ Installer built successfully!")
            # Parse output to find output file
            lines = process.stdout.split('\n')
            for line in lines:
                if "Successful compile" in line:
                    print(line)
        else:
            print("\n❌ Compilation failed!")
            print(process.stdout)
            print(process.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
