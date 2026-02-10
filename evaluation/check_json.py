import json
import requests
import time
from datetime import datetime
import os
import pandas as pd
import pdb
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import get_response, save_result, save_result_txt, extract_json, ensure_question_format
import random 
from utils import set_cache_path, init_writer, close_writer, load_file
import argparse

def parse_args():
	# 创建解析器
	parser = argparse.ArgumentParser(description="evaluate completeness of profile")
	# 添加参数
	parser.add_argument("--model", type=str, default="gpt-4o-mini")
	parser.add_argument("--entity_path", type=str, help="角色信息路径")
	parser.add_argument("--source", type=str, default="fandom", help="fandom | DRinfo")
	parser.add_argument("--entity_key", type=str, default=None, help="输入字段")
	parser.add_argument("--output_path", type=str, default="./knowledges/knowledge.json", help="输出文件路径")
	parser.add_argument("--pre_result", type=str, default=None, help="已有results路径")
     
	# 解析参数
	args = parser.parse_args()
	return args

args = parse_args()
print(args)
# exit()

# 配置方法选择
extract_model = args.model
# language = 'en'  # 选择 'zh' 或 'en'
entity_file = args.entity_path

pre_results_file = args.pre_result

# timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = args.output_path

parallel = True
max_workers = 5

set_cache_path('.cache-acg.pkl') # '.cache-' + output_file.replace('.json', '.pkl'))

progress_count = 0
progress_lock = threading.Lock()
total_entities = 0
save_interval = 100  # 每100个实体保存一次

PROMPTS = '''I have a JSON array that fails to parse with json.loads() due to invalid escape characters such as \'.
Please correct the JSON so that it becomes valid and can be successfully parsed.
You should:

- Fix all invalid escape sequences.
- Ensure every string is properly quoted.
- Return the corrected JSON only, without extra commentary.

Here is the JSON that needs to be corrected:
'''

def to_my_entity_key(entity_info):
	return entity_info[0]

def save_progress(results, filename=None):
	"""统一的保存进度函数"""
	if filename is None:
		filename = output_file
	
	os.makedirs(os.path.dirname(filename), exist_ok=True)
	with open(filename, 'w', encoding='utf-8') as f:
		json.dump(results, f, ensure_ascii=False, indent=2)


def process_entity(entity_info):
    """处理单个实体的函数，用于并发执行"""
    global progress_count, total_entities, invalid_cnt

    entity_name, entity_info = entity_info

    with progress_lock:
        progress_count += 1
        current = progress_count

    print(f"[{current}/{total_entities}] 开始处理实体: {entity_name}")

    # 保存完整的实体信息
    result = {
        'entity': entity_name
    } 

    messages = []

    if not isinstance(entity_info['response'], str):
        result['response'] = entity_info['response']
        return result
    
    prompt = PROMPTS + entity_info['response']
    
    # if pre_results.get(entity_name, None):
    #     if pre_results[entity_name].get('response', None):
    #         resp = pre_results[entity_name]['response']
    #         if isinstance(resp, dict):
    #             result['response'] = resp
    #             print('already extracted')
    #             return result

    messages.append({'role': 'user', 'content': prompt})
    knowledge = get_response(model=extract_model, messages=messages)
    try:
        knowledge = knowledge.strip('```').strip('json')
        result['response'] = json.loads(knowledge)
    except:
        print('cannot parse to json format')
        result['response'] = knowledge
        invalid_cnt += 1

    # 	# 离线判定答案唯一性 TODO
    return result

try:
    pre_results:dict = load_file(pre_results_file)
    print(pre_results_file, 'OK')
except:
    pre_results = dict()
    print('cannot open pre_results_file')

def main():
    global total_entities

    # 读取多个实体文件
    entities_data = []
    # 按优先级顺序读取各个文件
    with open(entity_file, 'r', encoding='utf-8') as f:
        df = json.load(f)
    print(f"成功读取 {entity_file}，共 {len(df)} 条记录")
		
    # 读取实体信息，添加到列表中，排除已有实体
    entities_data = list(df.items())

    # 展示popularity分布
    print(f"总共读取了 {len(entities_data)} 个实体")

    total_entities = len(entities_data)

    # 根据方法调整并发数
    # 初始化结果字典，包含已有结果和新实体
    results = {}

    if parallel:
        completed_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_entity = {executor.submit(process_entity, entity_info): to_my_entity_key(entity_info) for entity_info in entities_data}
            
            # 处理完成的任务
            for future in as_completed(future_to_entity):
                entity_key = future_to_entity[future]
                result = future.result()
                results[entity_key] = result
                completed_count += 1
                
                # 每100个实体保存一次
                if completed_count % save_interval == 0:
                    print(f"💾 已完成 {completed_count} 个实体，保存中间结果...")
                    save_progress(results)
                    print(f"💾 中间结果已保存: results/{output_file}")

    else:
        for i, entity_info in enumerate(entities_data, 1):
            result = process_entity(entity_info)
            results[to_my_entity_key(entity_info)] = result
            
            # 每100个实体保存一次
            if i % save_interval == 0:
                print(f"💾 已完成 {i} 个实体，保存中间结果...")
                save_progress(results)
                print(f"💾 中间结果已保存: results/{output_file}")

    # 统计结果：已有数据 + 新完成的数据
    total_completed = len([result for result in results.values() if result is not None])
    new_completed = len([result for entity_info in entities_data for result in [results[to_my_entity_key(entity_info)]] if result is not None])
    new_failed = len(entities_data) - new_completed

    print(f"📊 统计结果:")
    # print(f"  已有实体: {len(existing_entitiy_keys)}")
    print(f"  新处理实体: {len(entities_data)}")
    print(f"  新成功: {new_completed}, 新失败: {new_failed}")
    print(f"  总计成功: {total_completed}, 总计实体: {len(results)}")

    # 保存汇总结果
    save_progress(results, output_file)

    # 保存TXT格式的简化结果
    # save_result_txt(f'results/{output_file}_simple.txt', results)

    print(f"📄 JSON格式: results/{output_file}.json")
    # print(f"📄 TXT格式: results/{output_file}_simple.txt")

invalid_cnt = 0

if __name__ == "__main__":
    main()
    print(invalid_cnt)
    