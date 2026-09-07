#!/usr/bin/env python3
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1];dist=root/'dist'
if dist.exists():shutil.rmtree(dist)
shutil.copytree(root/'src',dist);shutil.copytree(root/'public',dist,dirs_exist_ok=True)
(dist/'.nojekyll').write_text('',encoding='utf-8')
print(dist)
