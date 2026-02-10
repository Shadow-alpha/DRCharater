"""
fandom_multi_community_crawler.py

功能：
1) 给定角色名（例如 "Tony Stark"），先尝试通过 Fandom 全局搜索 API 确定相关 communities（子域）。
2) 在每个 community 中使用该站点的 Search API 找到最相关的页面 URL（降级到构造 wiki URL）。
3) 抓取页面（BeautifulSoup）并解析 infobox + 各节文本，输出 JSON。
4) 将结果保存为 character.json

依赖：
pip install requests beautifulsoup4
"""

import requests
from bs4 import BeautifulSoup, Tag, NavigableString
import json
import re
import time
import urllib.parse
from collections import OrderedDict
from urllib.parse import quote
import os
from rapidfuzz import fuzz, process
from datetime import datetime


HEADERS = {"User-Agent": "YOUR_HEADER"}
REQUEST_TIMEOUT = 10

def call_json(url, params=None):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("JSON call failed:", e)
        return None

def call_text(url, params=None):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print("Text call failed:", e)
        return None

# ---------------------------
# Step 1: 先尝试用 Fandom 全局 Search API
# ---------------------------
## 对于某些community手动指定（直接搜索发现错误）
community_dict_path = "fran_community_dict_part.json"
with open(community_dict_path, 'r', encoding='utf-8') as f:
    community_dict = json.load(f)

def find_communities_via_rules(query: str):
    if query in community_dict:
        return community_dict[query]
    
    if "demon slayer" in query.lower():
        return "https://kimetsu-no-yaiba.fandom.com"
    if 'jojo' in query.lower():
        return "https://jojo.fandom.com"
    if 'konosuba' in query.lower():
        return "https://konosuba.fandom.com"
    if 'Dragon Ball' in query:
        return "https://dragonball.fandom.com"
    # if 'fate' in query.lower():
    #     return "https://fateuniverse.fandom.com"
    
    return None
    

def find_communities(query, limit=8):
    """
    尝试调用 fandom.com 的全局 Search API:
      https://www.fandom.com/api/v1/Search/List?query=...&limit=...
    该 API 有时会被限制或不可用。若成功，返回一组 (community_domain, page_url) 的候选。
    """

    url = find_communities_via_rules(query)
    if url:  return url
    
    base = "https://community.fandom.com/wiki/Special:SearchCommunity?scope=community"
    params = {"query": query, "limit": limit}
    data = call_text(base, params=params)
    communities = []
    if not data:
        return communities

    soup = BeautifulSoup(data, 'html.parser')
    a_tag = soup.select_one('.unified-search__result__title')

    if a_tag and a_tag.has_attr("href"):
        url = a_tag["href"]
        # print(url)
        return url
    else:
        print("未找到链接")
        return None


# ---------------------------
# Step 2: 在单个 community 里查询最相关 page（优先用 /api/v1/Search/List）
# ---------------------------
def get_best_page_in_community(query, community_domain, limit=10):
    """
    community_domain like 'https://marvel.fandom.com'
    返回 page_url 或 None
    """
    api_url = f"{community_domain.rstrip('/')}/api.php"
    params = {"action": "opensearch", "format": "json", "search": query, "limit": limit}
    # params = {"action": "query", "format": "json", "list": "categorymembers", "cmtitle": "Category:Characters_by_name", "cmlimit": min(50, limit)}
    data = call_json(api_url, params=params)

    if data[1]:
        best_tuple = process.extractOne(query, data[1], scorer=fuzz.token_sort_ratio)
        idx = best_tuple[2]
        return data[3][idx]
    else:
        return None


# ---------------------------
# Step 3: 解析角色页面（infobox + 分节）
# ---------------------------

def clean_invisible_chars(text: str) -> str:
    # 移除软连字符、零宽空格等常见不可见字符
    return re.sub(r'[\u00ad\u200b\u200c\u200d\u2060\ufeff]', '', text)

def remove_references(soup: BeautifulSoup, cls='.reference'):
    """删除所有 class=reference 的节点，避免脚注被提取。"""
    for ref in soup.select(cls):
        ref.decompose()

def extract_html_tree(node: Tag):
    if isinstance(node, str):
        return node.get_text()
    if not isinstance(node, Tag):
        return ""
    
    tagname = node.name.lower()
    if tagname == 'br':
        return '\n'

    if tagname in ['ul', 'ol']:
        child_texts = ""
        for li in node.find_all('li', recursive=False):
            child_texts += ('-' + extract_html_tree(li).strip() + '\n')
        return ' [ ' + child_texts.strip() + ' ] '
    
    if tagname == 'table':
        for tbody in node.find_all('tbody', recursive=False):
            table = []
            for tr in tbody.find_all('tr', recursive=False):
                rows = []
                for td in tr.find_all('td', recursive=False):
                    txt = extract_html_tree(td).strip()
                    if txt:  rows.append(txt)
                if rows:
                    table.append(' | '.join(rows))
            if table:
                return '{'+ '}\n{'.join(table) +'}'
            else:
                return ""
    
    if tagname == 'p':
        return node.get_text(" ", strip=True)
    
    child_texts = ""
    for child in node.children:
        text = extract_html_tree(child)
        child_texts += text

    if tagname == 'span':
        return child_texts.strip() + ' '
    else:
        return child_texts.strip() + '\n'


def parse_character_page(url):
    text = call_text(url)
    if not text:
        raise RuntimeError(f"无法获取页面: {url}")
    soup = BeautifulSoup(text, "html.parser")

    # 标题
    title_tag = soup.select_one("h1.page-header__title") or soup.select_one("#firstHeading") or soup.select_one("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # infobox: 常见 class .portable-infobox 或 .infobox
    infobox = {}
    # portable-infobox 风格
    for pi in soup.select(".portable-infobox"):
        for item in pi.select(".pi-item"):
            label_el = item.select_one(".pi-data-label")
            value_el = item.select_one(".pi-data-value")

            if label_el and value_el:
                remove_references(label_el)
                remove_references(value_el)
                # remove_references(value_el, '.extiw')

                key = label_el.get_text(" ", strip=True).strip()
                val = extract_html_tree(value_el).strip()
                key = clean_invisible_chars(key)
                infobox[key] = clean_invisible_chars(val)
    else:
        # 旧式 table.infobox
        table = soup.select_one("table.infobox")
        if table:
            for row in table.select("tr"):
                th = row.select_one("th")
                td = row.select_one("td")
                if th and td:
                    key = th.get_text(" ", strip=True)
                    val = td.get_text(" ", strip=True)
                    infobox[key] = val

    # 正文分节
    content = {}
    # 用 MediaWiki 主体 #mw-content-text 查找 h2/h3
    content_root = soup.select_one("#mw-content-text") or soup
    remove_references(content_root)
    # remove_references(content_root, '.extiw')
    remove_references(content_root, '.mw-editsection')
    remove_references(content_root, '.portable-infobox')

    headers = content_root.select("h2, h3, h4") if content_root else []
    titles = []
    for h in headers:
        # 过滤掉“参考文献”“外部链接”等不需要的部分后缀
        section_title = h.get_text(" ", strip=True).strip()
        if section_title.lower().strip() in ("参考资料", "参考", "注释", "注释和参考", "参考文献", "外部链接", "参见", "reference", "references", "navigation"):
            continue
        if h.name == 'h2':
            titles = [section_title]
        else:
            titles.append(section_title)
        texts = []
        for sib in h.find_next_siblings():
            if sib.name in ["h2", "h3", "h4"]:
                break
            if sib.name == "p":
                txt = sib.get_text(" ", strip=True)
            else:
                txt = extract_html_tree(sib).strip()

            if txt:
                texts.append(txt)

        if texts:
            key = clean_invisible_chars('--'.join(titles))
            content[key] = clean_invisible_chars("\n\n".join(texts))
        try:
            if sib.name in ["h2", "h3", "h4"]:
                pop_num = int(h.name[1]) - int(sib.name[1]) + 1
                for _ in range(pop_num): titles.pop()
        except:
            pass

    # fallback: if content empty, take first paragraphs
    if not content:
        paras = []
        for p in content_root.select("p")[:6]:
            t = p.get_text(" ", strip=True)
            if t:
                paras.append(t)
        if paras:
            content["summary"] = "\n\n".join(paras)

    return {
        "name": title,
        "url": url,
        "infobox": infobox,
        "content": content
    }


# ---------------------------
# 主流程封装
# ---------------------------
def crawl_character_find_best(query: str, max_communities=6):

    character_name = query.split('(')[0].strip() if '(' in query else query
    franchise_name = query.split('(', maxsplit=1)[-1][:-1].strip() if '(' in query else query
    # 1) 先试全局 API
    community_domain = find_communities(franchise_name, limit=max_communities)
    
    if not community_domain:
        raise RuntimeError("找不到任何 Fandom community，无法继续")

    print(f"查询站点 {community_domain} ...")
    page_url = get_best_page_in_community(character_name, community_domain)
    print(f'浏览网页 {page_url} ...')
    time.sleep(0.8)  # 友好延迟
    if page_url:
        results = parse_character_page(page_url)
        return results
    else:
        raise RuntimeError("在候选社区中未找到匹配页面")


def save_json(data, filename="character.json"):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------
# 获取文件列表
# ---------------------------
def get_character_list(path: str):
    if path.endswith('.json'):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return list(data.keys())
    
    elif path.endswith('jsonl'):
        with open(path, 'r', encoding='utf-8') as f:
            data = [json.loads(line) for line in f.readlines()]
            return [entity['name'] + f' ({entity["franchise"]})' for entity in data]
        
if __name__ == "__main__":

    character_path = "../getcharacter/acg_characters_v1.jsonl"
    character_list = get_character_list(character_path)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f"./gt/character_{timestamp}.json"
    save_interval = 10
    max_entries = 3

    results = {}
    for i, character in enumerate(character_list):
        t = 0
        while t < max_entries:
            try:
                res = crawl_character_find_best(character, max_communities=1)
                results[character] = res
                print(f"{character} 完成 ✅\n")
                break
            except Exception as e:
                results[character] = {'error': str(e)}
                print(f"{character} 失败：", e)
                t += 1
        
        if (i+1) % save_interval == 0:
            save_json(results, output_path)
            print(f"💾 已爬取{i+1}个角色，结果保存在{output_path}")
    
    save_json(results, output_path)
    print(f"📄全部{len(character_list)}个角色已完成，保存最终结果在{output_path}")
