#!/bin/bash

# =========================
# Global variables
# =========================
timestamp=$(date +"%Y%m%d_%H%M%S")
model=qwen3-235B

# Base directories
PROJECT_ROOT=/home/sjy/DRCharater-main
EVAL_SCRIPT=${PROJECT_ROOT}/completeness_evaluation.py

KNOWLEDGE_DIR=${PROJECT_ROOT}/evaluation/knowledges
FANDOM_GT=${PROJECT_ROOT}/fandom/gt/character_fandom.json

GEMINI_RESULT=${PROJECT_ROOT}/gen/results/gemini_search/gemini_acg_characters_profile.json
DOUBAO_RESULT=${PROJECT_ROOT}/gen/results/doubao_search/doubao_search_acg_characters_profile.json

OUTPUT_DIR=./results
mkdir -p ${OUTPUT_DIR}

# Knowledge files
FANDOM_KNOWLEDGE=${KNOWLEDGE_DIR}/${model}_fandom_knowledges.json
GEMINI_KNOWLEDGE=${KNOWLEDGE_DIR}/${model}_gemini-info_knowledges.json

# =========================
# 1. fandom knowledge vs gemini info
# =========================
echo "fandom knowledge vs gemini info"
python ${EVAL_SCRIPT} --model ${model} \
    --knowledge_path ${FANDOM_KNOWLEDGE} \
    --text_path ${GEMINI_RESULT} \
    --text_type DRinfo \
    --entity_key search_again_response \
    --output_path ${OUTPUT_DIR}/${model}_fandom_gemini-info_${timestamp}.json
    # --pre_result ${OUTPUT_DIR}/${model}_fandom_gemini-info_20251122_170530.json

# =========================
# 2. fandom knowledge vs gemini profile
# =========================
echo "fandom knowledge vs gemini profile"
python ${EVAL_SCRIPT} --model ${model} \
    --knowledge_path ${FANDOM_KNOWLEDGE} \
    --text_path ${GEMINI_RESULT} \
    --text_type profile \
    --entity_key english_profile \
    --output_path ${OUTPUT_DIR}/${model}_fandom_gemini-en-profile_${timestamp}.json

# =========================
# 3. fandom knowledge vs gemini info (ablation)
# =========================
echo "fandom knowledge vs gemini info ablation"
python ${EVAL_SCRIPT} --model ${model} \
    --knowledge_path ${FANDOM_KNOWLEDGE} \
    --text_path ${GEMINI_RESULT} \
    --text_type DRinfo \
    --entity_key search_response \
    --output_path ${OUTPUT_DIR}/${model}_fandom_gemini-info_ablation_${timestamp}.json

# =========================
# 4. gemini knowledge vs fandom info
# =========================
echo "gemini knowledge vs fandom info"
python ${EVAL_SCRIPT} --model ${model} \
    --knowledge_path ${GEMINI_KNOWLEDGE} \
    --text_path ${FANDOM_GT} \
    --text_type fandom \
    --output_path ${OUTPUT_DIR}/${model}_gemini-info_fandom_${timestamp}.json

# =========================
# 5. fandom knowledge vs doubao info
# =========================
echo "fandom knowledge vs doubao info"
python ${EVAL_SCRIPT} --model ${model} \
    --knowledge_path ${FANDOM_KNOWLEDGE} \
    --text_path ${DOUBAO_RESULT} \
    --text_type DRinfo \
    --entity_key search_response \
    --output_path ${OUTPUT_DIR}/${model}_fandom_doubao-info_${timestamp}.json

# =========================
# 6. fandom knowledge vs doubao profile
# =========================
echo "fandom knowledge vs doubao profile (EN)"
python ${EVAL_SCRIPT} --model ${model} \
    --knowledge_path ${FANDOM_KNOWLEDGE} \
    --text_path ${DOUBAO_RESULT} \
    --text_type profile \
    --entity_key english_profile \
    --output_path ${OUTPUT_DIR}/${model}_fandom_doubao-en-profile_${timestamp}.json

echo "fandom knowledge vs doubao profile (ZH)"
python ${EVAL_SCRIPT} --model ${model} \
    --knowledge_path ${FANDOM_KNOWLEDGE} \
    --text_path ${DOUBAO_RESULT} \
    --text_type profile \
    --entity_key chinese_profile \
    --output_path ${OUTPUT_DIR}/${model}_fandom_doubao-zh-profile_${timestamp}.json
