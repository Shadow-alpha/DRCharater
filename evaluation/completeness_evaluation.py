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
from utils import load_file, set_cache_path, init_writer, close_writer
import argparse

def parse_args():
	# 创建解析器
	parser = argparse.ArgumentParser(description="evaluate completeness of profile")
	# 添加参数
	parser.add_argument("--model", type=str, default="gpt-4o-mini")

	parser.add_argument("--knowledge_path", type=str, required=True, help="knowledge path")

	parser.add_argument("--text_type", type=str, default="profile", help="the path of profile searched by LLM")
	parser.add_argument("--text_path", type=str, required=True, help="the path of profile searched by LLM")
	parser.add_argument("--entity_key", type=str, default=None, help="输入对比的字段")
	parser.add_argument("--output_path", type=str, required=True, help="输出文件路径")
	parser.add_argument("--pre_result", type=str, default=None, help="已有results路径")

	# 解析参数
	args = parser.parse_args()
	return args

args = parse_args()
print(args)

# 配置方法选择
compare_model = args.model
# language = 'zh'  # 选择 'zh' 或 'en'
# profile_method = 'doubao_search'

# profile_file = "D:/复旦大学/研究生/RPLA/DRCharater-main/gen/results/gemini_search/gemini_acg_characters_old.json"
profile_file = args.text_path
gt_konwledge_file = args.knowledge_path

pre_results_file = args.pre_result

# timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = args.output_path

parallel = True
max_workers = 10

set_cache_path('.cache-acg.pkl') # '.cache-' + output_file.replace('.json', '.pkl'))

progress_count = 0
progress_lock = threading.Lock()
total_entities = 0
save_interval = 10  # 每100个实体保存一次

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

	entity_name, knowledge_list, character_text = entity_info

	with progress_lock:
		progress_count += 1
		current = progress_count

	print(f"[{current}/{total_entities}] 开始比较实体: {entity_name}")

	pre_result = pre_results.get(entity_name, None)
	# 保存完整的实体信息
	result = {
		'entity': entity_name,
	} 

	## has been evaluated
	if pre_result and isinstance(pre_result.get('response', None), list):
		result['response'] = pre_result['response']
		return result

	from prompt import COMPARE_PROMPT

	messages = []

	prompt = COMPARE_PROMPT.replace('{knowledge_list}', json.dumps(knowledge_list, ensure_ascii=False, indent=2)).replace('{character_text}', character_text)
	messages.append({'role': 'user', 'content': prompt})

	response = get_response(model=compare_model, messages=messages)
	
	try:
		response = response.strip('```').strip('json')
		response = json.loads(response)
	except:
		invalid_cnt += 1
		print('cannot parse to json format')

	result['response'] = response

	if response is None:
		return result

	# 	# 离线判定答案唯一性 TODO
	return result

def get_input_data():
	gt = load_file(gt_konwledge_file)
	print(f"成功读取 {gt_konwledge_file}，共 {len(gt)} 条记录")
	profile_full = load_file(profile_file)
	print(f"成功读取 {profile_file}，共 {len(profile_full)} 条记录")
	
	entity_key = args.entity_key
	# if language == 'en':  entity_key = 'english_profile'
	# elif language == 'zh': entity_key = 'chinese_profile'

	entities_data = []
	for entity_name in gt.keys():
		if not isinstance(gt[entity_name]['response'], dict) or not gt[entity_name]['response'].get('knowledge_points', None): continue
		if entity_name in profile_full:
			knowledges = gt[entity_name]['response']['knowledge_points']
			knowledge_list = [{'id': i, 'knowledge': knowledge['knowledge']} for i, knowledge in enumerate(knowledges, start=1)]
			if entity_key is None and profile_full[entity_name]:
				character_text = json.dumps(profile_full[entity_name], ensure_ascii=False)
				entities_data.append((entity_name, knowledge_list, character_text))
			elif profile_full[entity_name].get(entity_key, None):
				character_text = profile_full[entity_name][entity_key]
				entities_data.append((entity_name, knowledge_list, character_text))

	return entities_data


def main():
	global total_entities
	
	# 展示popularity分布
	entities_data = get_input_data()
	print(f"总共读取了 {len(entities_data)} 个实体")
	
	total_entities = len(entities_data)

	# init_writer(f"{search_model}_response.jsonl")
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

	# print(f"📁 结果保存在 results/ 目录下（使用{profiling_model}方法）")
	print(f"📄 JSON格式: results/{output_file}.json")
	# print(f"📄 TXT格式: results/{output_file}_simple.txt")

	# close_writer()

invalid_cnt = 0

if __name__ == "__main__":
	try: 
		with open(pre_results_file, 'r', encoding='utf-8') as f:
			pre_results: dict = json.load(f)
			print(pre_results_file)
	except:
		pre_results = dict()
		print('no previous results or fail to parse')
	main()
	print('invalid: ', invalid_cnt)