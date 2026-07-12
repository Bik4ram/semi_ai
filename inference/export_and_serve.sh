#!/bin/bash
# Merge the final LoRA adapter into the base model, convert to GGUF,
# quantize, and serve locally. Unlike the previous version, every
# step here actually executes -- nothing is commented out.
#
# Run this AFTER whichever stage you consider your "final" model
# (DPO or GRPO). Set FINAL_STAGE below.
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FINAL_STAGE="${1:-dpo-lora}"   # pass grpo-lora as arg1 if you ran stage 4
ADAPTER_DIR="${PROJECT_DIR}/models/${FINAL_STAGE}"
MERGED_DIR="${PROJECT_DIR}/models/merged-full"
GGUF_DIR="${PROJECT_DIR}/models/merged-gguf"

if [ ! -d "$ADAPTER_DIR" ]; then
  echo "ERROR: $ADAPTER_DIR not found. Run the training stages first, or pass the correct stage name."
  exit 1
fi

echo "=== Step 1: Merge LoRA adapter into full-precision weights ==="
mkdir -p "$MERGED_DIR"
python3 - <<PYEOF
from unsloth import FastLanguageModel
model, tok = FastLanguageModel.from_pretrained("${ADAPTER_DIR}", max_seq_length=2048, load_in_4bit=False)
model.save_pretrained_merged("${MERGED_DIR}", tok, save_method="merged_16bit")
print("Merged model saved to ${MERGED_DIR}")
PYEOF

echo "=== Step 2: Clone and build llama.cpp (only if not already built) ==="
if [ ! -d "${PROJECT_DIR}/llama.cpp" ]; then
  git clone --depth 1 https://github.com/ggml-org/llama.cpp "${PROJECT_DIR}/llama.cpp"
fi
cmake -B "${PROJECT_DIR}/llama.cpp/build" -S "${PROJECT_DIR}/llama.cpp"
cmake --build "${PROJECT_DIR}/llama.cpp/build" --config Release -j

echo "=== Step 3: Convert to GGUF and quantize ==="
mkdir -p "$GGUF_DIR"
python3 "${PROJECT_DIR}/llama.cpp/convert_hf_to_gguf.py" "$MERGED_DIR" --outfile "${GGUF_DIR}/model.gguf"
"${PROJECT_DIR}/llama.cpp/build/bin/llama-quantize" "${GGUF_DIR}/model.gguf" "${GGUF_DIR}/model.Q4_K_M.gguf" Q4_K_M

echo "=== Step 4: Start server ==="
echo "Run this in a separate terminal (or background it with &):"
echo "  ${PROJECT_DIR}/llama.cpp/build/bin/llama-server -m ${GGUF_DIR}/model.Q4_K_M.gguf --port 8080"
echo "Then test it with:"
echo '  curl http://localhost:8080/completion -d '"'"'{"prompt": "Explain this SV module: module mux2(input sel,a,b, output y); assign y = sel?b:a; endmodule"}'"'"
