import matplotlib.pyplot as plt
from utils import load_file
import argparse
from collections import defaultdict
import pandas as pd

label_map = {'supportive': 'supported', 'unsupported': 'contradicted', 'partial support': 'partially supported', 'relevant': 'supported'}

def arg_parse():
    parser = argparse.ArgumentParser(description="这是一个示例程序")
    parser.add_argument('--results_path', type=str, required=True, help='结果路径')
    # parser.add_argument('--age', type=int, default=18, help='年龄，默认为18')
    args = parser.parse_args()
    return args


def count_knowledges():
    pass

def get_metrics(result: dict):
    supported = result.get('supported', 0)
    partially_supported = result.get('partially supported', 0)
    irrelevant = result.get('irrelevant', 0)
    contradicted = result.get('contradicted', 0)

    total = supported + partially_supported + irrelevant + contradicted
    recall = (supported + 0.5*partially_supported) / total
    contradict_rate = contradicted / total

    return {
        "total": total,
        "recall": recall,
        "contradict_rate": contradict_rate
    }

def evaluate_total(results):
    ent_cnt = defaultdict(int)
    for entity_name, info in results.items():
        result = info['response']
        if not isinstance(result, list): continue
        for res in result:
            label = label_map.get(res['evaluation'], res['evaluation'])
            ent_cnt[label] += 1
    return ent_cnt

def evaluate_type(knowledges, results):
    type_entity_counter = defaultdict(lambda : defaultdict(int))

    valid = 0
    for entity_name, info in results.items():
        result = info['response']
        knowledge = knowledges[entity_name]['response']['knowledge_points']

        if not isinstance(result, list) or not isinstance(knowledge, list): continue
        for res, k in zip(result, knowledge):
            tp = k['type']
            label = label_map.get(res['evaluation'], res['evaluation'])
            type_entity_counter[tp][label] += 1
        valid += 1
    print('valid: ', valid)

    table = []
    for tp, cnt in type_entity_counter.items():
        metrics = get_metrics(cnt)
        table.append({'type': tp, **metrics})

    return pd.DataFrame(table)

def is_valid(knowledge):
    if knowledge.get('response', None):
        if isinstance(knowledge['response'], dict) and knowledge['response'].get('knowledge_points', None):
            knowledge_list = knowledge['response']['knowledge_points']
            if isinstance(knowledge_list, list) and len(knowledge_list) > 0:
                return True
    return False


if __name__ == "__main__":
    args = arg_parse()
    knowledges_path = "./knowledges/qwen3-235B_fandom_knowledges_retyped.json"
    results_path = args.results_path
    results = load_file(results_path)
    knowledges = load_file(knowledges_path)

    
    print("knowledges: ", len([1 for v in knowledges.values() if is_valid(v)]))
    print("results: ", len(results))
    print(evaluate_type(knowledges, results))
