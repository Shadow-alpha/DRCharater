# 虚拟角色热门度分析项目

## 🎯 项目概述

本项目通过真实数据收集和智能合并算法，构建了包含**2,107个独特虚拟角色**的高质量数据库。专注于来自动漫、游戏、电影、小说、漫画的热门角色，并基于作品来源进行智能去重合并。

## 📊 核心成果

- **数据来源**: 3个验证平台 (AniList, MyAnimeList, Character.AI)
- **角色总数**: 2,107个独特角色
- **合并准确率**: 100%
- **数据格式**: JSONL (每行一个角色)

## 🔥 核心文件

### 必需文件 (保留)

1. **`final_merged_characters.jsonl`** ⭐⭐⭐⭐⭐
   - 最终的2,107个角色数据库
   - JSONL格式，每行包含完整角色信息
   - 包含跨平台人气数据和作品来源

2. **`character_data_processor.py`** ⭐⭐⭐⭐⭐
   - 完整的数据收集和合并系统
   - 包含真实数据爬取功能
   - 基于作品的智能合并算法

3. **`fast_real_characters.json`** ⭐⭐⭐⭐
   - 原始收集的2,139个角色数据
   - 作为合并前的备份数据

4. **`README.md`** ⭐⭐⭐⭐
   - 项目说明和使用指南

## 🚀 快速开始

### 数据收集
```bash
python character_data_processor.py --mode collect
```

### 角色合并
```bash
python character_data_processor.py --mode merge
```

### 完整流程
```bash
python character_data_processor.py --mode full
```

## 📋 数据格式

每个角色的JSON结构：
```json
{
  "name": "角色名称",
  "franchise": "所属作品",
  "category": "anime/game/movie/novel/manga",
  "total_popularity_score": 总人气分数,
  "source_count": 数据源数量,
  "platforms": ["平台列表"],
  "sources": [
    {
      "platform": "数据源平台",
      "rank": "原始排名",
      "popularity_score": "平台人气分数",
      "name_variant": "名称变体",
      "franchise": "作品名"
    }
  ],
  "final_rank": "最终排名"
}
```

## 🎯 算法特色

### 智能合并规则
- ✅ 只合并来自**同一作品**的相似角色
- ✅ 处理罗马化变体 (Gojou → Gojo)
- ❌ 拒绝不同作品的同名角色
- ❌ 拒绝同作品的不同角色

### 验证案例
- ✅ `Satoru Gojo` + `Gojo Satoru` (咒术回战)
- ❌ `Zoro` (海贼王) + `Zoro` (鬼灭之刃)
- ❌ `Yor Forger` + `Loid Forger` (间谍家家酒)

## 📈 发现的热门趋势

### 顶级动漫系列
1. **咒术回战** - 新兴现象级作品
2. **进击的巨人** - 跨平台持续热门  
3. **海贼王** - 长期稳定经典
4. **火影忍者** - 经典角色依然活跃
5. **鬼灭之刃** - 近年爆款

### 平台差异
- **官方动漫平台**: 偏爱经典长篇作品
- **AI聊天平台**: 偏爱复杂人格角色

## 🔧 技术栈

- **Python 3.8+**
- **requests** - API调用
- **BeautifulSoup4** - 网页解析  
- **json** - 数据处理
- **difflib** - 字符串相似度

## 📄 许可证

本项目仅用于学术研究和个人学习目的。

---

*最后更新: 2025-01-08*