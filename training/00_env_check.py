#!/usr/bin/env python3
"""
Run this FIRST, every time, before any training script. It tells you
honestly what you have to work with, so nothing silently falls back
to a fake toy model the way the previous version did.
"""
import shutil
import subprocess
import sys


def check_gpu():
    try:
        import torch
    except ImportError:
        print("[FAIL] torch not installed. Run: pip install torch")
        return False
    if not torch.cuda.is_available():
        print("[WARN] No CUDA GPU detected. Training a 1.5B-7B model here "
              "will be VERY slow or infeasible. Use Google Colab "
              "(Runtime -> Change runtime type -> T4 GPU, it's free) instead.")
        return False
    name = torch.cuda.get_device_name(0)
    mem_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"[OK] GPU detected: {name} ({mem_gb:.1f} GB VRAM)")
    if mem_gb < 12:
        print("[WARN] Under 12GB VRAM -- stick to the 1.5B base model and "
              "small batch sizes / 4-bit QLoRA.")
    return True


def check_pkg(name, import_name=None):
    import_name = import_name or name
    try:
        __import__(import_name)
        print(f"[OK] {name} importable")
        return True
    except ImportError:
        print(f"[FAIL] {name} not installed. Run: pip install {name}")
        return False


def check_verilator():
    if shutil.which("verilator"):
        out = subprocess.run(["verilator", "--version"], capture_output=True, text=True)
        print(f"[OK] verilator installed: {out.stdout.strip()}")
        return True
    print("[WARN] verilator not found. Lint-verification of generated SV/SVA "
          "will be skipped. Install with: sudo apt install verilator "
          "(on Colab: !apt-get -y install verilator)")
    return False


if __name__ == "__main__":
    print("=== Environment check ===")
    ok_gpu = check_gpu()
    ok_unsloth = check_pkg("unsloth")
    ok_trl = check_pkg("trl")
    ok_peft = check_pkg("peft")
    ok_bnb = check_pkg("bitsandbytes")
    ok_verilator = check_verilator()
    print("=== Summary ===")
    if ok_gpu and ok_unsloth and ok_trl and ok_peft:
        print("Ready to train for real. Proceed to 10_cpt_train.py.")
    else:
        print("NOT ready -- fix the [FAIL] items above before proceeding. "
              "Do not let anything silently substitute a fake model.")
        sys.exit(1)
