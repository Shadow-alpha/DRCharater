# CharacterHub

This repository contains the official code and resources for the paper **CharacterHub: Open-Domain Character Profiling for LLM Role-play via Deep Search**.

The project focuses on:
- Constructing compact, information-dense character profiles from heterogeneous web sources
- Evaluating profile completeness and faithfulness against reference knowledge
- Analyzing common bias patterns in character profile generation

---

## 1. Environment Setup

We recommend using **Python 3.10** and managing dependencies via **conda**.

```bash
conda create -n DRCharacter python=3.10
conda activate DRCharacter
```

Install required packages:
```bash
pip install -r requirements.txt
```

## 2. Profile Construction

### 2.1 Character Collection

Character name collection and preprocessing scripts are provided in the `getcharacter/` directory.

Please refer to the scripts in this folder for details on character crawling and filtering.

### 2.2 Profile Generation

To generate character profiles using the proposed deep-search-based pipeline:

```bash
cd gen

python gen_wiki.py
```

## 3. Profile Evaluation

We evaluate character profiles by measuring their knowledge completeness and density against reference knowledge extracted from curated sources.

### 3.1 Fandom Reference

First, construct fandom-based reference data:

```bash
cd fandom

python fandom_character_info.py
```

### 3.2 Reference Knowledge Extraction
Next, convert reference data into atomic knowledge units for evaluation:

```bash
cd evaluation

bash scrips/knowledge.sh
```

### 3.3 Completeness Evaluation
Run completeness evaluation using a judging LLM:

```bash
bash scrips/compare.sh
```

### 3.4 Metrics

Detailed evaluation results and analysis are provided in `evaluation/evaluate.ipynb`

Alternatively, metrics can be computed directly via:
```bash
python metrics.py --konwledges_path qwen3-235B_fandom_knowledges.json --results_path qwen3-235B_fandom_gemini-info.json
```