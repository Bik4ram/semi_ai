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

echo "Cloning UVM-Examples (Apache-2.0, comprehensive UVM examples)..."
[ -d UVM-Examples ] || git clone --depth 1 https://github.com/SeanOBoyle/UVM-Examples

echo "Cloning UVM-Core (Apache-2.0, official UVM library)..."
[ -d uvm-core ] || git clone --depth 1 https://github.com/accellera-official/uvm-core

echo "Cloning Core-V-Verif (Apache-2.0, industrial UVM verification environment)..."
[ -d core-v-verif ] || git clone --depth 1 https://github.com/openhwgroup/core-v-verif

echo "Cloning CORE-V Cores (Apache-2.0)..."
[ -d core-v-cores ] || git clone --depth 1 https://github.com/openhwgroup/core-v-cores

echo "Cloning CV32E40P (Apache-2.0, RTL + DV)..."
[ -d cv32e40p ] || git clone --depth 1 https://github.com/openhwgroup/cv32e40p

echo "Cloning CV32E40X (Apache-2.0, RTL + DV)..."
[ -d cv32e40x ] || git clone --depth 1 https://github.com/openhwgroup/cv32e40x

echo "Cloning CV32E40S (Apache-2.0, RTL + DV)..."
[ -d cv32e40s ] || git clone --depth 1 https://github.com/openhwgroup/cv32e40s

echo "Cloning CVA6 (Apache-2.0, 64-bit RISC-V RTL)..."
[ -d cva6 ] || git clone --depth 1 https://github.com/openhwgroup/cva6

echo "Cloning Ibex (Apache-2.0, RTL + DV)..."
[ -d ibex ] || git clone --depth 1 https://github.com/lowRISC/ibex

echo "Cloning PicoRV32 (ISC License)..."
[ -d picorv32 ] || git clone --depth 1 https://github.com/YosysHQ/picorv32

echo "Cloning PULP AXI (Apache-2.0, AXI RTL + Verification)..."
[ -d axi ] || git clone --depth 1 https://github.com/pulp-platform/axi

echo "Cloning AXI UVM VIP (MIT)..."
[ -d axi-uvm ] || git clone --depth 1 https://github.com/marcoz001/axi-uvm

echo "Cloning AXI (Alex Forencich, MIT)..."
[ -d verilog-axi ] || git clone --depth 1 https://github.com/alexforencich/verilog-axi

echo "Cloning Wishbone/AXI Verification (Apache-2.0)..."
[ -d wb2axip ] || git clone --depth 1 https://github.com/ZipCPU/wb2axip

echo "Cloning APB Components..."
[ -d apb ] || git clone --depth 1 https://github.com/pulp-platform/apb

echo "Cloning Common Cells (Verification utilities)..."
[ -d common_cells ] || git clone --depth 1 https://github.com/pulp-platform/common_cells

echo "Cloning Register Interface (regtool)..."
[ -d register_interface ] || git clone --depth 1 https://github.com/pulp-platform/register_interface

echo "Cloning Bender (dependency manager)..."
[ -d bender ] || git clone --depth 1 https://github.com/pulp-platform/bender

echo "Cloning OpenTitan (Apache-2.0)..."
[ -d opentitan ] || git clone --depth 1 https://github.com/lowRISC/opentitan

echo "Sparse-cloning OpenTitan DV environments..."
if [ ! -d opentitan_dv ]; then
    git clone --filter=blob:none --sparse --depth 1 https://github.com/lowRISC/opentitan opentitan_dv
    cd opentitan_dv
    git sparse-checkout set \
        hw/ip/uart/dv \
        hw/ip/i2c/dv \
        hw/ip/spi_device/dv \
        hw/ip/gpio/dv \
        hw/ip/aes/dv \
        hw/ip/kmac/dv \
        hw/ip/flash_ctrl/dv \
        hw/ip/rv_timer/dv \
        hw/ip/hmac/dv \
        hw/ip/otbn/dv \
        hw/ip/pwm/dv \
        hw/ip/keymgr/dv \
        hw/ip/csrng/dv
    cd ..
fi

echo "Sparse-cloning OpenTitan Register Generator..."
if [ ! -d opentitan_reggen ]; then
    git clone --filter=blob:none --sparse --depth 1 https://github.com/lowRISC/opentitan opentitan_reggen
    cd opentitan_reggen
    git sparse-checkout set util/reggen
    cd ..
fi

echo "Cloning SV-Tests (Apache-2.0)..."
[ -d sv-tests ] || git clone --depth 1 https://github.com/chipsalliance/sv-tests

echo "Cloning Surelog (Apache-2.0, SystemVerilog Parser)..."
[ -d Surelog ] || git clone --depth 1 https://github.com/chipsalliance/Surelog

echo "Cloning UHDM (Apache-2.0)..."
[ -d UHDM ] || git clone --depth 1 https://github.com/chipsalliance/UHDM

echo "Cloning Verible (Apache-2.0, Formatter/Linter)..."
[ -d verible ] || git clone --depth 1 https://github.com/chipsalliance/verible

echo "Cloning Verilator (LGPL-3.0, Simulator)..."
[ -d verilator ] || git clone --depth 1 https://github.com/verilator/verilator

echo "Cloning Yosys (ISC License)..."
[ -d yosys ] || git clone --depth 1 https://github.com/YosysHQ/yosys

echo "Cloning SymbiYosys (Formal Verification)..."
[ -d sby ] || git clone --depth 1 https://github.com/YosysHQ/sby

echo "Cloning Cocotb (BSD-3)..."
[ -d cocotb ] || git clone --depth 1 https://github.com/cocotb/cocotb

echo "Cloning Cocotb Bus..."
[ -d cocotb-bus ] || git clone --depth 1 https://github.com/cocotb/cocotb-bus

echo "Cloning PyUVM..."
[ -d pyuvm ] || git clone --depth 1 https://github.com/pyuvm/pyuvm

echo "Cloning FuseSoC..."
[ -d fusesoc ] || git clone --depth 1 https://github.com/olofk/fusesoc

echo "Cloning Edalize..."
[ -d edalize ] || git clone --depth 1 https://github.com/olofk/edalize

echo "Cloning RISC-V Architectural Tests..."
[ -d riscv-arch-test ] || git clone --depth 1 https://github.com/riscv-non-isa/riscv-arch-test

echo "Cloning RISC-V DV Generator..."
[ -d riscv-dv ] || git clone --depth 1 https://github.com/chipsalliance/riscv-dv

echo "Cloning RISC-V ISA Simulator (Spike)..."
[ -d riscv-isa-sim ] || git clone --depth 1 https://github.com/riscv-software-src/riscv-isa-sim

echo "Cloning Rocket Chip..."
[ -d rocket-chip ] || git clone --depth 1 https://github.com/chipsalliance/rocket-chip

echo "Cloning Chipyard..."
[ -d chipyard ] || git clone --depth 1 https://github.com/ucb-bar/chipyard

echo "Cloning OpenROAD..."
[ -d OpenROAD ] || git clone --depth 1 https://github.com/The-OpenROAD-Project/OpenROAD

echo "Cloning OpenLane..."
[ -d OpenLane ] || git clone --depth 1 https://github.com/The-OpenROAD-Project/OpenLane



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
