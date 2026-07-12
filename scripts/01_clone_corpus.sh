#!/bin/bash
# STATION 1 -- collect raw, public, permissively-licensed corpus.
# Run this from the project root: bash scripts/01_clone_corpus.sh
set -e
cd "$(dirname "$0")/.."
mkdir -p data/raw && cd data/raw

echo "Cloning picorv32 (ISC license, tiny RV32 core)..."
[ -d picorv32 ] || git clone --depth 1 https://github.com/YosysHQ/picorv32

echo "Cloning ibex (Apache-2.0, production-quality RV32 core + DV env)..."
[ -d ibex ] || git clone --depth 1 https://github.com/lowRISC/ibex

echo "Cloning uvm-core (Apache-2.0, the actual UVM base class library)..."
[ -d uvm-core ] || git clone --depth 1 https://github.com/accellera-official/uvm-core

echo "Sparse-cloning a few OpenTitan peripherals (Apache-2.0, register-map examples)..."
if [ ! -d opentitan ]; then
  git clone --filter=blob:none --sparse --depth 1 https://github.com/lowRISC/opentitan
  cd opentitan
  git sparse-checkout set hw/ip/i2c hw/ip/uart hw/ip/spi_device
  cd ..
fi

echo "Cloning riscv-arch-test (golden-reference compliance suite)..."
[ -d riscv-arch-test ] || git clone --depth 1 https://github.com/riscv-software-src/riscv-arch-test

cd - > /dev/null
echo ""
echo "=== Corpus collected ==="
du -sh data/raw/* 2>/dev/null || true
echo ""
echo "Recording provenance in data/sources.md ..."
cat > data/sources.md << 'EOF'
# Data Sources

| Repository | URL | License |
|---|---|---|
| picorv32 | https://github.com/YosysHQ/picorv32 | ISC |
| ibex | https://github.com/lowRISC/ibex | Apache-2.0 |
| uvm-core | https://github.com/accellera-official/uvm-core | Apache-2.0 |
| opentitan (i2c, uart, spi_device only) | https://github.com/lowRISC/opentitan | Apache-2.0 |
| riscv-arch-test | https://github.com/riscv-software-src/riscv-arch-test | BSD/CC-BY (per-file, see repo) |

All sources are public, open-source, and permissively licensed for both
inspection and training use. No proprietary or company data is included.
EOF
echo "Done."
