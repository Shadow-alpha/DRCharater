from fandom_character_info import parse_character_page, community_dict, crawl_character_find_best
import json
import os

def split_name_francise(s: str):
    name = s.split('(')[0].strip()
    francise = s.split('(', maxsplit=1)[-1][:-1].strip()
    return name, francise

def save_json(data, filename="character.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

modified = list(community_dict.keys())[-1:]
def is_modify(fran):
    if fran in modified:
        return True
    return False

if __name__ == "__main__":
    input_path = "./gt/character_fandom_latest.json"
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    modified_data = dict()
    for char, info in data.items():
        name, fran = split_name_francise(char)
        if is_modify(fran):
            data[char] = crawl_character_find_best(char)
            modified_data[char] = data[char]
    save_json(data, './gt/character_fandom_latest.json')
    save_json(modified_data, 'modified_char.json')