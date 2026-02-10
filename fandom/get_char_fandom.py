import json
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# ====== 配置区 ======
WIKI_BASE = "https://attackontitan.fandom.com"   # 换成你的 Fandom 主站
OUTPUT_FILE = "character.json"
RATE_LIMIT = 0.5        # 秒
# ====================

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0"
})

def get_soup(url):
    resp = SESSION.get(url, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def search_get_top_page(char_name):
    """用 Fandom 自带搜索，返回最匹配的角色页 url"""
    search_url = f"{WIKI_BASE}/api.php?action=opensearch&search={quote(char_name)}&limit=1&format=json"
    # search_url = f"{WIKI_BASE}/api.php?action=opensearch&search=Levi Ackerman&format=json"

    data = SESSION.get(search_url, timeout=15).json()
    # print('search_get_top_page: ', data)
    # data[3] 是返回的 url 列表
    return data[3][0] if data[3] else None

def parse_infobox(character_url):
    """解析右侧 infobox 表格为 dict"""
    soup = get_soup(character_url)
    data = {"url": character_url, "name": soup.select_one("h1").get_text(strip=True)}
    # print(data)
    # 标题
    title_tag = soup.select_one("h1.page-header__title") or soup.select_one("#firstHeading") or soup.select_one("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # infobox: 常见 class .portable-infobox 或 .infobox
    infobox = {}
    # portable-infobox 风格
    pi = soup.select_one(".portable-infobox")
    if pi:
        for item in pi.select(".pi-item"):
            label = item.select_one(".pi-data-label")
            value = item.select_one(".pi-data-value")
            if label and value:
                infobox[label.get_text(" ", strip=True)] = value.get_text(" ", strip=True)
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
    headers = content_root.select("h2, h3") if content_root else []

    for h in headers:
        # 过滤掉“参考文献”“外部链接”等不需要的部分后缀
        section_title = h.get_text(" ", strip=True)
        if section_title.lower().strip() in ("参考资料", "参考", "注释", "注释和参考", "参考文献", "外部链接", "参见"):
            continue
        texts = []
        for sib in h.find_next_siblings():
            if sib.name in ["h2", "h3"]:
                break
            if sib.name == "p":
                txt = sib.get_text(" ", strip=True)
                if txt:
                    texts.append(txt)
        if texts:
            content[section_title] = "\n\n".join(texts)

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
        "url": character_url,
        "infobox": infobox,
        "content": content
    }

def main():
    raw = input("请输入角色名（多个用逗号或空格分隔）：\n> ")
    names = re.split(r"[,\s]+", raw.strip())
    # names = ["Levi Ackerman", "Eren Yeager"]
    results = {}
    for name in names:
        if not name:
            continue
        print(f"[+] 正在查询：{name}")
        try:
            url = search_get_top_page(name)
            print('url: ', url)
            if not url:
                results[name] = {"error": "未找到对应页面"}
                continue
            results[name] = parse_infobox(url)
        except Exception as e:
            results[name] = {"error": str(e)}
        time.sleep(RATE_LIMIT)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"全部完成！结果已写入 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()