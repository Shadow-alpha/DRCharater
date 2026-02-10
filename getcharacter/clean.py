import json
with open('final_merged_characters.jsonl', 'r') as f:
    data = []
    for line in f:
        d = json.loads(line)
        if d['franchise'] != '':
            data.append(d)

print(len(data))

with open('acg_characters_v1.jsonl', 'w') as f:
    for item in data:
        f.write(json.dumps(item) + '\n')
