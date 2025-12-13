import os
import shutil

ROOT = r"d:\Documents\Active\StrategyAnalysisPlatform"
BACKEND_DIR = os.path.join(ROOT, "backend")

# Items to KEEP in ROOT (Do Not Move)
KEEP = {
    ".git", 
    ".gitignore",
    "frontend", 
    "exporters", 
    "docs", 
    "backend", # The destination itself
    "organize_backend.py", # This script
    ".venv", # Virtual environments break if moved; keep or leave for user to handle
    "StrategyAnalysisPlatform.code-workspace"
}

def organize():
    if not os.path.exists(BACKEND_DIR):
        os.makedirs(BACKEND_DIR)
        print(f"Created {BACKEND_DIR}")

    # List all items in ROOT
    items = os.listdir(ROOT)
    
    for item in items:
        if item in KEEP:
            continue
            
        src_path = os.path.join(ROOT, item)
        dest_path = os.path.join(BACKEND_DIR, item)
        
        print(f"Moving {item} -> backend/")
        try:
            shutil.move(src_path, dest_path)
        except Exception as e:
            print(f"  Error moving {item}: {e}")

if __name__ == "__main__":
    organize()
