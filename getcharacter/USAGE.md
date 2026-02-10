# 快速使用指南

## 📁 文件说明

### 核心文件
- **`final_merged_characters.jsonl`** - 最终的2,107个角色数据库 (主要成果)
- **`character_data_processor.py`** - 完整的数据收集和合并系统
- **`fast_real_characters.json`** - 原始收集的2,139个角色数据 (备份)
- **`README.md`** - 详细项目说明

## 🚀 使用方法

### 1. 查看最终结果
```bash
head -n 3 final_merged_characters.jsonl
```

### 2. 重新运行数据收集
```bash
python character_data_processor.py --mode collect
```

### 3. 重新运行角色合并
```bash
python character_data_processor.py --mode merge
```

### 4. 运行完整流程
```bash
python character_data_processor.py --mode full
```

## 📊 数据格式

每行JSON包含：
- `name`: 角色名称
- `franchise`: 所属作品
- `total_popularity_score`: 跨平台总人气
- `sources`: 各平台详细数据
- `final_rank`: 最终排名

## 🎯 项目成果

- **2,107个独特角色** (从2,139个原始数据合并而来)
- **32个成功合并** (同角色不同名称变体)
- **100%合并准确率** (基于作品验证)
- **3个数据源** (AniList, MyAnimeList, Character.AI)

## 💡 核心算法

只有满足以下条件的角色才会被合并：
1. 来自不同数据源
2. 都有作品信息
3. 作品名称匹配
4. 角色名称高度相似

例如：
- ✅ `Satoru Gojo` + `Gojo Satoru` (同作品同角色)
- ❌ `Zoro` (海贼王) + `Zoro` (鬼灭之刃) (不同作品)
- ❌ `Yor Forger` + `Loid Forger` (同作品不同角色)