CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
vllm serve /data/models/Qwen/Qwen3-235B-A22B-Instruct-2507 \
    --tensor-parallel-size 8 \
    --max-model-len 200000 \
    --port 8001 \
    --trust-remote-code \
    --gpu-memory-utilization 0.9


# VLLM_ATTENTION_BACKEND=DUAL_CHUNK_FLASH_ATTN VLLM_USE_V1=0 \
# vllm serve /data/models/Qwen/Qwen3-235B-A22B-Instruct-2507 \
#   --tensor-parallel-size 8 \
#   --max-model-len 1010000 \
#   --enable-chunked-prefill \
#   --max-num-batched-tokens 131072 \
#   --enforce-eager \
#   --max-num-seqs 1 \
#   --gpu-memory-utilization 0.85
