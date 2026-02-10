from utils import get_response, load_file
import json

TYPES = ["identity", "appearance", "ability", "relationship", "experience", "personality", "other"]

model = "qwen3-235B"
knowledge_path = "./knowledges/qwen3-235B_gemini-info_knowledges.json"

prompt_templete = '''You are an expert knowledge classifier.  
Your task is to read each knowledge statement about a character and determine what category of information it represents.  
The output must be exactly one of the following seven categories:

  - identity: factual identity, origin, birthplace, nationality, species, titles, nicknames, ranks, aliases, professions, affiliations with organizations, teams, clans, groups, and roles or statuses associated with them.  
  - appearance: physical traits, looks, body, clothing, colors, and distinctive visual features.  
  - ability: skills, powers, techniques, magic, fighting capability, special talents, or combat style.  
  - relationship: family members, friends, rivals, lovers, allies, enemies, or any significant social/character connections.  
  - experience: key life events, battles, training, missions, achievements, historical background, or things the character has done.  
  - personality: temperament, behavior patterns, motivations, desires, goals, attitudes, emotional tendencies, moral stance, or thinking style.  
  - other: anything that does not reasonably fit into the above categories.

---

Input knowledge:
"{knowledge}"

---

Output format (strict JSON):
{"type": "<one_of_the_nine_categories>"}'''

if __name__ == "__main__":
    knowledges = load_file(knowledge_path)

    cnt = 0
    for char, info in knowledges.items():
        try:
            knowledge_list = info['response']['knowledge_points']
        except:
            continue

        # knowledge_list = [item for item in knowledge_list if 'knowledge' in item]
        for item in knowledge_list:
            if item['type'] not in TYPES:
                prompt = prompt_templete.replace('{knowledge}', item['knowledge'])
                messages = [{'role': 'user', 'content': prompt}]
                resp = get_response(model=model, messages=messages)
                try:
                    tp = json.loads(resp)['type']
                except:
                    tp = resp
                item['type'] = tp

        info['response']['knowledge_points'] = knowledge_list

    with open('./knowledges/qwen3-235B_gemini-info_knowledges_retyped.json', 'w', encoding='utf-8') as f:
        json.dump(knowledges, f, ensure_ascii=False, indent=2)