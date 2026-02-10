# EXTRACTION_PROMPT = '''现在你将获得一段从Fandom网站爬取到的的角色数据(JSON格式)，包含角色的基本信息（infobox）与正文描述（content）。请你对输入的JSON数据中的角色信息进行解析，提取角色相关的**知识点（knowledge items）**，并标注其类型与来源（infobox 或 content），每个知识点应是语义上完整的事实性信息或明确特征。例如：“Levi Ackerman 的身高是 160 cm” 或 “他是人类中最强的士兵”。以统一结构化格式输出结果。

# ### 注意应忽略对角色扮演无关的信息类型，包括以下信息：
# - 声优、演员、制作公司、出版商、集数或章节号。  
# - 统计性或外部信息（登场次数、票选结果、粉丝称号）。  
# - 对角色的外部评论或元信息（如“在动画第X集首次登场”）。    
# - 不属于角色世界内的meta描述。

# ### 尽量保留包括但不限于以下信息：
# - **basic_info**：如姓名、年龄、性别、生日、种族、身高、体重、出生地、状态（Alive/Dead）。  
# - **appearance**：外貌特征（发色、眼睛、体型、服装等）。  
# - **ability**：技能、战斗能力、称号、排名、成绩等。  
# - **relationship**：亲属、同伴、敌人、师徒、下属等关系。  
# - **experience**：重大事件、经历、成长背景、角色弧线。  
# - **affiliation**：组织、所属部队、职业、职位等。  
# - **personality**：性格特征或心理倾向（若有）。  
# - **title**：称号或绰号（如“人类最强士兵”）。  
# - **statistic**：数量性信息（如击杀数、成绩等级等）。  
# - **other**：不属于以上类别的其他显著事实。

# ### 输出格式
# 请以JSON格式输出，结构如下：

# {
#   "entity": "角色名",
#   "knowledge_points": [
#     {
#       "type": "basic_info | appearance | ability | relationship | experience | affiliation | personality | title | statistic | other",
#       "source": "infobox | content",
#       "evidence": "对应字段原文或句子",
#       "knowledge": "抽取的知识" 
#     },
#     ...
#   ]
# }
 

# ### 要求
# 1. 对于每一条字段或描述，提取出语义清晰、可独立成立并对“理解和扮演该角色”有帮助知识点。
# 2. 可将多个相关信息融合为单条语义完整的知识点。
# 3. 若信息不明确（如“early 30s”），可保留原表达。  
# 4. 确保输出为合法JSON，字段完整且分类合理。 
# 5. 如果信息无法确定，可省略该类别，不必填 "unknown"。

# ### 输入数据
# {input_json}'''


# ### Try to include information but is not limited to:
# - **basic_info**: age, gender, birthday, species, height, weight, birthplace, current status (Alive/Dead).  
# - **appearance**: physical features (hair color, eye color, body type, clothing, etc.).  
# - **ability**: skills, combat abilities, titles, rankings, performance.  
# - **relationship**: relatives, companions, enemies, mentors, subordinates, etc.  
# - **experience**: major events, personal history, development arc.  
# - **affiliation**: organizations, corps, occupations, ranks, positions.  
# - **personality**: character traits or psychological tendencies.  
# - **title**: honorifics or in-universe epithets (e.g., “Humanity’s Strongest Soldier”).  
# - **statistic**: numerical or quantitative facts (e.g., number of Titan kills, performance grades).  
# - **other**: any other notable facts not fitting the above categories.

extraction_details = '''
Each knowledge item should represent a semantically complete factual statement or a clearly defined attribute.  
For example: "He is a passionate young man determined to XXX" or "He is humanity's strongest soldier."  
Output the results in a unified structured format.

---

### Please IGNORE any information that is irrelevant to character role-playing, including:
- Field echo information that only restates a label or name (e.g. "His name is XXX.").  
- Voice actors, performers, production companies, publishers, episode or chapter numbers (e.g., “voiced by ...”).  
- Language, romanization, or spelling variants (e.g. Kanji, Romaji, kana notation).  
- Generic or obvious facts that do not distinguish this character from ordinary people (e.g. "He is human" or "He is male"), unless they have clear narrative or psychological significance (e.g. "He is human but can transform into a giant"--At this point, "human" information has semantic value).  
- Statistical or external information (e.g., number of appearances, popularity rankings, fan titles).  
- External commentary or meta descriptions about the character (e.g., “first appeared in episode X”).  
- Any meta-level information not belonging to the character's in-universe context.

---

### Output Format

Please output your result in JSON format as follows:

{
  "entity": "Character Name",
  "knowledge_points": [
    {
      "type": "identity | appearance | ability | relationship | experience | personality | other",
      "evidence": "Original supporting text or sentence from the input",
      "knowledge": "Extracted knowledge statement"
    },
    ...
  ]
}

---

### Rules

1. Each knowledge item should be semantically clear, self-contained, and useful for **understanding or role-playing the character**.  
2. Merge and deduplicate overlapping or equivalent facts. 
  - Keep only one representative version of each unique fact. Do not output two items that share the same meaning even if worded differently.  
  - If two statements express similar meaning, combine them into one richer description. 
3. **Do NOT invent or infer** beyond the text. If something is only hinted at or ambiguous, exclude it.  
4. Ensure the output is valid JSON with complete and logically consistent fields.  
5. If certain categories are not present, you may omit them — do not fill with "unknown".  
6. You must only use the following nine categories for `type`:
  - identity: factual identity, origin, birthplace, nationality, species, titles, nicknames, ranks, aliases, professions, affiliations with organizations, teams, clans, groups, and roles or statuses associated with them.  
  - appearance: physical traits, looks, body, clothing, colors, and distinctive visual features.  
  - ability: skills, powers, techniques, magic, fighting capability, special talents, or combat style.  
  - relationship: family members, friends, rivals, lovers, allies, enemies, or any significant social/character connections.  
  - experience: key life events, battles, training, missions, achievements, historical background, or things the character has done.  
  - personality: temperament, behavior patterns, motivations, desires, goals, attitudes, emotional tendencies, moral stance, or thinking style.  
  - other: anything that does not reasonably fit into the above categories.
  Do **not** create or use any other category.

---

### Input Data
{input_text}'''

EXTRACTION_PROMPT = {
"fandom": '''You will receive a piece of character data (in JSON format) crawled from the Fandom website.  
The data includes the character's basic information (infobox) and textual descriptions (content).  
Please parse the input JSON and extract all **knowledge items** related to the character, and focus on *meaningful*, *distinctive*, and *role-relevant* information that contributes to understanding or role-playing this character, labeling each item with its type.  
''' + extraction_details,

"DRinfo": '''You will receive a piece of textual data (e.g., search results or LLM-generated summaries) that describes a fictional character.  
Please extract all **knowledge items** related to the character, and focus on *meaningful*, *distinctive*, and *role-relevant* information that contributes to understanding or role-playing this character, labeling each item with its type.  
''' + extraction_details
}


COMPARE_PROMPT = '''You are an expert evaluator for role-playing character consistency.

### Task
You will receive two items:
1. `knowledge_list`: a JSON array of knowledge objects about a character, each describing a factual aspect of the character. Each object has:
   - "id": a unique integer identifier for the knowledge item,
   - "knowledge": a concise factual statement about the character.

2. `text`: a piece of character-related text. This may be:
   - a first-person profile written from the character's perspective,
   - a third-person descriptive text about the character,
   - or structured JSON data crawled from a source such as Fandom.  
   Treat all three forms uniformly as sources of factual claims.


Your goal is to determine, for each knowledge item in `knowledge_list`, determine whether the provided `text`:
- **supported**: The text explicitly expresses or clearly implies this knowledge point.
- **partially supported**: The text supports some but not all aspects of the knowledge point (e.g., mentions part of a list or partial causation).
- **irrelevant**: The text does not mention or relate to this knowledge point.
- **contradicted**: The text states or implies something that conflicts with this knowledge point.
Do NOT use any labels other than the four above.

### Important Rules
1. Focus on **semantic meaning**, not wording.  
  Example: if the knowledge says “He is calm and collected” and the text says “I rarely lose my temper,” that is **Supported**.  
2. A **Contradicted** label should be used only if the text explicitly or implicitly rejects or reverses something of the fact.  
3. Missing details or partial lack of coverage should be labeled **Irrelevant**, not Contradicted.  
4. **Do NOT treat narrative perspective or tense as evidence.**  
  - Do **NOT** interpret first-person narration (“I”) or present tense (“I am”, “I do”) as evidence that the character is alive or active in the current timeline. Only mark a contradiction if the text explicitly denies or reverses the fact (e.g., says “I’m still alive” versus a knowledge point stating “The character is dead”). Otherwise, mark as **Irrelevant**.
  - Do NOT treat tense differences as contradiction. If the knowledge describes a *past* identity, affiliation, role, or state (e.g., “former student”, “once belonged to”, “previously served as”), and the text describes a *present* identity that can naturally follow from it, then mark as **supported**, unless the text explicitly denies the past identity.
5. When uncertain, choose the most reasonable interpretation based on the content of the given text.
6. For each evaluation, provide a brief quote or reasoning from the text that justifies your judgment.

### Output requirements 
- **Return ONLY valid JSON**, and nothing else. The JSON must parse with `json.loads()`.  
- Output a JSON array of objects, one object per input knowledge item, preserving the input ids. Each object must have exactly these fields:
  - "id": (the integer id from the input)
  - "knowledge": (the original knowledge string copied verbatim from input)
  - "evaluation": one of "supported", "partially supported", "irrelevant", "contradicted"
  - "evidence": a short quote or concise reasoning from the text that justifies the evaluation

### Example
knowledge_list:
[
  {"id": 1, "knowledge": "Eren was born in the Shiganshina District."},
  {"id": 2, "knowledge": "Eren is calm and patient."},
  {"id": 3, "knowledge": "Eren can transform into a Titan."}
]

text:
"I grew up behind the walls of Shiganshina, dreaming of the world beyond. 
I've always been reckless and driven by anger — patience was never my strength. 
But since that day, I've carried the Titan power within me."

**Expected Output:**
[
  {
    "id": 1,
    "knowledge": "Eren was born in the Shiganshina District.",
    "evaluation": "supported",
    "evidence": "He says he grew up in Shiganshina."
  },
  {
    "id": 2,
    "knowledge": "Eren is calm and patient.",
    "evaluation": "contradicted",
    "evidence": "He describes himself as reckless and impatient."
  },
  {
    "id": 3,
    "knowledge": "Eren can transform into a Titan.",
    "evaluation": "supported",
    "evidence": "He mentions carrying the Titan power within him."
  }
]

### Input
knowledge_list:
{knowledge_list}

text:
{character_text}'''