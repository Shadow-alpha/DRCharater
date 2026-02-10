timestamp=$(date +"%Y%m%d_%H%M%S")
model=qwen3-235B

PROJECT_ROOT=/home/sjy/DRCharater-main

FANDOM_GT=${PROJECT_ROOT}/fandom/gt/character_fandom.json
GEMINI_RESULT=${PROJECT_ROOT}/gen/results/gemini_search/gemini_acg_characters_profile.json

python knowledge_extraction.py --model $model \
    --source fandom \
    --entity_path $FANDOM_GT \
    --output_path ./knowledges/"$model"_fandom.json \


echo "fandom OK"

python knowledge_extraction.py --model $model \
    --source DRinfo \
    --entity_path $GEMINI_RESULT \
    --output_path ./knowledges/"$model"_gemini-info.json \
    --entity_key search_again_response