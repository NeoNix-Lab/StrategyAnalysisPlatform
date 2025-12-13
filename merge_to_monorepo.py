import os
import shutil
import glob

# Configuration
DEST_ROOT = r"d:\Documents\Active\StrategyAnalysisPlatform"
SOURCES = {
    "frontend": r"d:\Documents\Active\StrategyAnalysisDashboard",
    "exporters/quantower": r"d:\Documents\Active\StrategyExporterTemplate"
}

# Ignore Patterns (Simple Glob list)
IGNORES = [
    ".git", ".vs", ".vscode", ".idea",
    "node_modules", "dist", "build", "coverage",
    "bin", "obj", "*.user", "*.suo",
    "__pycache__", ".venv", "venv", "*.db", "*.log"
]

def is_ignored(path, names):
    ignored = set()
    for name in names:
        for pattern in IGNORES:
            if glob.fnmatch.fnmatch(name, pattern):
                ignored.add(name)
                break
    return ignored

def merge_projects():
    print(f"Starting Monorepo Merge into {DEST_ROOT}...")
    
    for subpath, source_dir in SOURCES.items():
        dest_dir = os.path.join(DEST_ROOT, subpath)
        print(f"\nProcessing {subpath}...")
        print(f"  Source: {source_dir}")
        print(f"  Dest:   {dest_dir}")
        
        if os.path.exists(dest_dir):
            print("  Destination exists. Removing to ensure clean copy...")
            try:
                shutil.rmtree(dest_dir)
            except Exception as e:
                print(f"  WARNING: Could not remove directory {dest_dir}: {e}")
                # continue or retry?
        
        print(f"  Copying tree...")
        try:
            shutil.copytree(source_dir, dest_dir, ignore=is_ignored)
            print("  Success.")
        except Exception as e:
            print(f"  ERROR copying {source_dir}: {e}")

    print("\nMerge Complete.")

if __name__ == "__main__":
    merge_projects()
