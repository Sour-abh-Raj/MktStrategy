import os
from pathlib import Path

def scan_dir(p):
    large_files = []
    fifty_mb = 50 * 1024 * 1024
    ten_mb = 10 * 1024 * 1024
    for root, _, files in os.walk(p):
        if '.git' in root: continue
        for f in files:
            path = Path(root) / f
            try:
                size = path.stat().st_size
                if size > ten_mb:
                    large_files.append((str(path), size))
            except:
                pass
    large_files.sort(key=lambda x: x[1], reverse=True)
    return large_files

res = scan_dir('.')
with open('large.txt', 'w') as f:
    for path, size in res:
        f.write(f"{path} - {size / 1024 / 1024:.2f} MB\n")
