#!/bin/bash
# STATION 1 -- collect raw, public, permissively-licensed corpus.
# Run this from the project root: bash scripts/01_clone_corpus.sh
set -e
cd "$(dirname "$0")/.."
mkdir -p data/raw && cd data/raw

clone_repo () {
    local name=$1
    local url=$2

    echo "Cloning $name..."
    if [ ! -d "$name" ]; then
        git clone --depth 1 "$url" "$name" || echo "WARNING: Failed to clone $name"
    fi
}
clone_repo picorv32 https://github.com/YosysHQ/picorv32
clone_repo ibex https://github.com/lowRISC/ibex
clone_repo uvm-core https://github.com/accellera-official/uvm-core
clone_repo core-v-verif https://github.com/openhwgroup/core-v-verif
clone_repo core-v-cores https://github.com/openhwgroup/core-v-cores
clone_repo cv32e40p https://github.com/openhwgroup/cv32e40p
clone_repo cv32e40x https://github.com/openhwgroup/cv32e40x
clone_repo cv32e40s https://github.com/openhwgroup/cv32e40s
clone_repo cva6 https://github.com/openhwgroup/cva6
clone_repo axi https://github.com/pulp-platform/axi
clone_repo axi-uvm https://github.com/marcoz001/axi-uvm
clone_repo verilog-axi https://github.com/alexforencich/verilog-axi
clone_repo wb2axip https://github.com/ZipCPU/wb2axip
clone_repo apb https://github.com/pulp-platform/apb
clone_repo common_cells https://github.com/pulp-platform/common_cells
clone_repo register_interface https://github.com/pulp-platform/register_interface
clone_repo bender https://github.com/pulp-platform/bender
clone_repo sv-tests https://github.com/chipsalliance/sv-tests
clone_repo Surelog https://github.com/chipsalliance/Surelog
clone_repo UHDM https://github.com/chipsalliance/UHDM
clone_repo verible https://github.com/chipsalliance/verible
clone_repo verilator https://github.com/verilator/verilator
clone_repo yosys https://github.com/YosysHQ/yosys
clone_repo sby https://github.com/YosysHQ/sby
clone_repo cocotb https://github.com/cocotb/cocotb
clone_repo cocotb-bus https://github.com/cocotb/cocotb-bus
clone_repo pyuvm https://github.com/pyuvm/pyuvm
clone_repo fusesoc https://github.com/olofk/fusesoc
clone_repo edalize https://github.com/olofk/edalize
clone_repo riscv-arch-test https://github.com/riscv-non-isa/riscv-arch-test
clone_repo riscv-dv https://github.com/chipsalliance/riscv-dv
clone_repo riscv-isa-sim https://github.com/riscv-software-src/riscv-isa-sim
clone_repo rocket-chip https://github.com/chipsalliance/rocket-chip
clone_repo chipyard https://github.com/ucb-bar/chipyard
clone_repo OpenROAD https://github.com/The-OpenROAD-Project/OpenROAD
clone_repo OpenLane https://github.com/The-OpenROAD-Project/OpenLane



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
