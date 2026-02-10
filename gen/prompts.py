# Language configuration
PROMPTS = {
    'zh': {
        'search_prompt': """请帮我搜集关于'{entity}'的所有相关知识，整合成一份详细的百科式的资料。使用markdown格式。务必真实、综合、全面，不遗漏重要信息。你要甄别信息的真实性、信息源的可信度，不要包含或编造虚假的信息。""",
        
        'search_second_prompt': """请继续搜索，对你已经搜集到的知识进行验证和扩充，比如搜索密切相关的人物、事件、物品等实体。""",
    },
    'en': {
        'search_prompt': """Please help me collect all relevant knowledge about '{entity}' and integrate it into a detailed encyclopedic document. Use markdown format. Be truthful, comprehensive, and thorough, without omitting important information. You must verify the authenticity of information and the credibility of sources. Do not include or fabricate false information.""",
        
        'search_second_prompt': """Please continue searching to verify and expand on the knowledge you have already collected, such as searching for closely related people, events, objects, and other entities.""",
    }
}

def get_prompt(prompt_name, language='zh'):
    """
    Get a prompt in the specified language.
    
    Args:
        prompt_name (str): Name of the prompt ('search_prompt', 'search_second_prompt', 'question_generate_prompt')
        language (str): Language code ('zh' for Chinese, 'en' for English)
    
    Returns:
        str: The prompt in the specified language
    """
    if language not in PROMPTS:
        raise ValueError(f"Unsupported language: {language}. Supported languages: {list(PROMPTS.keys())}")
    
    if prompt_name not in PROMPTS[language]:
        raise ValueError(f"Prompt '{prompt_name}' not found for language '{language}'")
    
    return PROMPTS[language][prompt_name]

# Backward compatibility - keep the original variables for 'zh' (Chinese)
search_prompt = PROMPTS['zh']['search_prompt']
search_second_prompt = PROMPTS['zh']['search_second_prompt'] 


PROMPT_DEEP_SEARCH = {'en': '''Please help me collect all relevant knowledge about '{entity}' and integrate it into a detailed encyclopedic document. Use markdown format. You must verify the authenticity of information and the credibility of sources to ensure accuracy, and avoid fabricated or false information. You should include the character's personality (very important), background, physical description, core motivations, notable attributes, relationships, key experiences, major plot involvement and key decisions or actions, character arc or development throughout the story, if there is any information about these aspects.
Continue searching to expand on the knowledge already collected. You should include not only information about {entity} directly, but also closely related people, events, objects, organizations, and other entities that contribute to understanding {entity}.
Present the collected information as a detailed encyclopedic-style document in Markdown and ensure the document is well-structured, clear, comprehensive and thorough, without omitting important details.''',
'zh':'''请帮我收集所有与'{entity}'相关的知识，并将其整合成一份详细的百科式文档（使用 Markdown 格式）。你必须核实信息的真实性和来源的可信度，以确保内容准确，避免虚构或错误的信息。文档中应当包括（如果有关于这些方面的信息）该角色的性格（非常重要）、背景与出身、外貌描述、核心动机、显著特征、人际关系、关键经历、主要情节参与和关键决策或行动、角色弧线或在故事中的发展。
继续搜索以扩展已收集的知识。不仅限于 {entity} 本身的信息，还应包括与其密切相关的人物、事件、物品、组织和其他有助于理解 {entity} 的实体。
以 Markdown 格式呈现所收集的信息，作为一份详细的百科全书风格文档，确保文档结构清晰、逻辑合理、内容全面详尽，不遗漏重要细节'''}