#!/usr/bin/env python3
"""
CoSER-Llama-3.1-70B 模型下载脚本
使用 hf-mirror.com 镜像加速下载
"""

import os
import sys
from pathlib import Path

# 设置 Hugging Face 镜像源
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("错误: 未安装 huggingface_hub")
    print("请运行: pip install huggingface_hub")
    sys.exit(1)

# 模型信息
MODEL_REPO = "Qwen/Qwen3-235B-A22B-Instruct-2507"
MODEL_DIR = "~/models/Qwen/Qwen3-235B-A22B-Instruct-2507"

print("=" * 50)
print(f"{MODEL_REPO} 模型下载脚本")
print(f"镜像源: {os.environ['HF_ENDPOINT']}")
print(f"模型仓库: {MODEL_REPO}")
print(f"保存目录: {MODEL_DIR}")
print("=" * 50)
print()

try:
    print("开始下载模型...")
    print("提示: 这是一个 235B 参数的大模型，文件约 470GB")
    print("下载可能需要较长时间，请耐心等待...")
    print()

    # 下载模型
    snapshot_download(
        repo_id=MODEL_REPO,
        local_dir=MODEL_DIR,
        local_dir_use_symlinks=False,
        resume_download=True,  # 支持断点续传
    )

    print()
    print("=" * 50)
    print(f"下载完成！模型保存在: {MODEL_DIR}")
    print("=" * 50)

except KeyboardInterrupt:
    print("\n\n下载已取消")
    print("提示: 下次运行脚本时会自动从断点继续下载")
    sys.exit(1)
except Exception as e:
    print(f"\n错误: {e}")
    print("\n可能的解决方案:")
    print("1. 检查网络连接")
    print("2. 确认磁盘空间充足 (需要约 140GB)")
    print("3. 检查是否有权限写入目录")
    sys.exit(1)

