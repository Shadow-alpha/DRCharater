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
from utils import set_cache_path, init_writer, close_writer

# 配置方法选择
search_model = 'gemini_search' # 'gemini_search' or 'doubao_search'
profiling_model = 'qwen'
language = 'en'  # choose 'zh' or 'en'
if_translated = True
translate_model = "qwen"

# results_file = "./results/gemini_search/gemini_profile.json"
# results_file = "./results/doubao_search_acg_characters_v1_output_20251026_141356.json"

entity_files = ['../getcharacter/acg_characters_v1.jsonl']
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'{search_model}_acg_characters_v1_output_{timestamp}.json'
existing_files = []
parallel = True
max_workers = 3

set_cache_path('.cache-acg.pkl') # '.cache-' + output_file.replace('.json', '.pkl'))

progress_count = 0
progress_lock = threading.Lock()
total_entities = 0
save_interval = 10  # 每10个实体保存一次

def to_my_entity_key(entity_info):
	if 'entity_info' in entity_info:
		return entity_info['entity_info']['label'] + f' ({entity_info["franchise"]})'
	else:
		return  entity_info['label'] + f' ({entity_info["franchise"]})'

def save_progress(results, filename=None):
	"""统一的保存进度函数"""
	if filename is None:
		filename = output_file
	
	os.makedirs("results", exist_ok=True)
	with open(f'results/{filename}', 'w', encoding='utf-8') as f:
		json.dump(results, f, ensure_ascii=False, indent=2)

def process_entity(entity_info):
	"""处理单个实体的函数，用于并发执行"""
	global progress_count, total_entities

	entity_name = entity_info['label']
	entity_description = f'{entity_info["franchise"]}'
	
	with progress_lock:
		progress_count += 1
		current = progress_count
	
	print(f"[{current}/{total_entities}] 开始查询实体: {entity_name}")
	
	# 保存完整的实体信息
	result = {
		'entity': entity_name,
		'entity_info': entity_info.to_dict() if hasattr(entity_info, 'to_dict') else entity_info
	} 

	pre_result = total_results.get(to_my_entity_key(entity_info), None)
	
	if search_model == "gemini_search":
		from prompts import get_prompt

		messages = []

		# 搜集实体信息 - 第一次使用label + description
		search_prompt = get_prompt('search_prompt', language) + "You should include the character's personality (very important), background, physical description, core motivations, notable attributes, relationships, key experiences, major plot involvement and key decisions or actions, character arc or development throughout the story, if there is any information about these aspects."
		entity_full = f"{entity_name} ({entity_description})" if entity_description else entity_name
		prompt = search_prompt.replace('{entity}', entity_full, 1).replace('{entity}', entity_name)
		messages.append({'role': 'user', 'content': prompt})
		if pre_result and pre_result.get('search_response', None):
			knowledge = pre_result['search_response']
			print('search response already exist')
		else:
			knowledge = get_response(model=search_model, messages=messages)
		result['search_response'] = knowledge
		messages.append({'role': 'assistant', 'content': knowledge})

		if knowledge is None:
			return result

		# 二次扩展
		search_second_prompt = get_prompt('search_second_prompt', language)
		messages.append({'role': 'user', 'content': search_second_prompt})
		if pre_result and pre_result.get('search_again_response', None):
			knowledge2 = pre_result['search_again_response']
			print('search again response already exist')
		else:
			knowledge2 = get_response(model=search_model, messages=messages)
		result['search_again_response'] = knowledge2
		messages.append({'role': 'assistant', 'content': knowledge2})

		if knowledge2 is None:
			return result

	elif search_model == "doubao_search":
		from prompts import PROMPT_DEEP_SEARCH
		messages = []

		# 搜集实体信息 - 第一次使用label + description
		search_prompt = PROMPT_DEEP_SEARCH[language]
		entity_full = f"{entity_name} ({entity_description})" if entity_description else entity_name
		prompt = search_prompt.replace('{entity}', entity_full, 1).replace('{entity}', entity_name)
		messages.append({'role': 'user', 'content': prompt})
		if pre_result and pre_result.get('search_response', None):
			knowledge = pre_result['search_response']
			print('search response already exist')
		else:
			knowledge = get_response(model=search_model, messages=messages)
		result['search_response'] = knowledge
		messages.append({'role': 'assistant', 'content': knowledge})

		if knowledge is None:
			return result

	# 生成问题 - 后续只使用label
	if language == 'en':
		profiling_prompt = "Please completely rewrite all the above information from {entity}'s first-person perspective. Ensure that the information is comprehensive and accurate. You need to focus on the character's personality, which you could also analyze based on the characters' experiences. Besides, include include the character's, background, physical description, core motivations, notable attributes, relationships, key experiences, major plot involvement and key decisions or actions, character arc or development throughout the story, and other important details, if they appear in the information that you obtained."
	elif language == 'zh':
		profiling_prompt = "请将上述所有信息完全改写为以 {entity} 的第一人称视角叙述的形式。确保信息全面且准确。你需要重点描写角色的性格，也可以结合角色的经历进行分析。此外，如果信息中有，还应包括角色的背景出身、外貌描写、核心动机、显著特征、人际关系、关键经历、主要剧情参与和重要决策或行动、角色弧线或在故事中的发展，以及你所获取信息中出现的其他重要细节。"
	
	profiling_prompt = profiling_prompt.replace('{entity}', entity_name)
		
	messages.append({'role': 'user', 'content': profiling_prompt})

	if language == 'en':
		k1, k2 = 'english_profile', 'chinese_profile'
	elif language == 'zh':
		k1, k2 = 'chinese_profile', 'english_profile'
	
	if pre_result and pre_result.get(k1, None):
			profile = pre_result[k1]
			print(f'{k1} already exist')
	else:
		profile = get_response(model=profiling_model, messages=messages)
		
	result[k1] = profile

	if profile is None:
		return result

	if if_translated:
		if language == 'en':
			translation_prompt = "我会给你一段关于{entity}的第一人称视角的自我介绍。你请将它忠实地翻译为中文。不要遗漏任何信息。"
		elif language == 'zh':
			translation_prompt = "I will provide you with a self-introduction written from the first-person perspective of {entity}. Please translate it into English faithfully, without omitting any information."
		translation_prompt = translation_prompt.replace('{entity}', entity_name) + '\n\n' + profile

		if pre_result and pre_result.get(k2, None):
			translated_profile = pre_result[k2]
			print(f'{k2} already exist')
		else:
			translated_profile = get_response(model=translate_model, messages=[{'role': 'user', 'content': translation_prompt}])

		result[k2] = translated_profile

	# result['chinese_profile'] = zh_profile
	# 	# 离线判定答案唯一性 TODO
	return result

def load_file(path: str):
	data = []
	if path.endswith('.csv'):
		df = pd.read_csv(path)
		for _, row in df.iterrows():
			entity_dict = row.to_dict()
			data.append(entity_dict)

	elif path.endswith('.json'):
		with open(path, 'r', encoding='utf-8') as f:
			json_data = json.load(f)
			if isinstance(json_data, list):
				data = json_data
			elif isinstance(json_data, dict):
				data = [v['entity_info'] for k, v in json_data.items()]
			else:
				raise NotImplementedError(f'can not parse file {path}')
	else:
		raise NotImplementedError(f'can not parse file {path}')
	
	print(f"成功读取 {path}，共 {len(data)} 条记录")
	return data

try:
	with open(results_file, 'r', encoding='utf-8') as f:
		total_results: dict = json.load(f)
except:
	total_results = dict()

def main():
	global total_entities
	
	# 读取多个实体文件
	entities_data = []
	n_entities = 10100
	# 按优先级顺序读取各个文件
	for i_f, entity_file in enumerate(entity_files):
		_entities_data = load_file(entity_file)
		# df = pd.read_csv(entity_file)
		# print(f"成功读取 {entity_file}，共 {len(df)} 条记录")
		
		# 读取实体信息，添加到列表中，排除已有实体
		# _entities_data = []
		# for _, row in df.iterrows():
		# 	entity_dict = row.to_dict()
		# 	_entities_data.append(entity_dict)
		
		entities_data.extend(_entities_data)

	# 展示popularity分布
	entities_data = entities_data
	print(f"总共读取了 {len(entities_data)} 个实体")
	
	total_entities = len(entities_data)

	# init_writer(f"results/{search_model}/{timestamp}_response.jsonl")
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
	save_result_txt(f'results/{output_file}_simple.txt', results)

	print(f"📁 结果保存在 results/ 目录下（使用{profiling_model}方法）")
	print(f"📄 JSON格式: results/{output_file}.json")
	print(f"📄 TXT格式: results/{output_file}_simple.txt")

	# close_writer()

if __name__ == "__main__":
	main()
