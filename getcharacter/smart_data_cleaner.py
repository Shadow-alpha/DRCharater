#!/usr/bin/env python3
"""
Smart Data Cleaner - Fix duplicate issues intelligently
"""

import json
import re
from typing import List, Dict, Set
from difflib import SequenceMatcher
from collections import defaultdict

class SmartDataCleaner:
    def __init__(self):
        # Only clean obvious duplicates and fix known franchise issues
        self.manual_fixes = {
            # Fix known characters without franchise from MAL
            'Lelouch Lamperouge': 'Code Geass',
            'C.C.': 'Code Geass',
            'Luffy Monkey D.': 'One Piece',
            'Zoro Roronoa': 'One Piece',
            'Levi': 'Attack on Titan',
            'L Lawliet': 'Death Note',
            'Light Yagami': 'Death Note',
            'Killua Zoldyck': 'Hunter x Hunter',
            'Edward Elric': 'Fullmetal Alchemist',
            'Alphonse Elric': 'Fullmetal Alchemist',
            'Rintarou Okabe': 'Steins;Gate',
            'Kurisu Makise': 'Steins;Gate',
            'Goku Son': 'Dragon Ball',
            'Vegeta': 'Dragon Ball',
            'Ichigo Kurosaki': 'Bleach',
            'Rukia Kuchiki': 'Bleach',
            'Naruto Uzumaki': 'Naruto',
            'Sasuke Uchiha': 'Naruto',
            'Itachi Uchiha': 'Naruto',
            'Kakashi Hatake': 'Naruto',
            'Eren Yeager': 'Attack on Titan',
            'Mikasa Ackerman': 'Attack on Titan',
            'Armin Arlert': 'Attack on Titan',
            'Erwin Smith': 'Attack on Titan',
            'Hange Zoë': 'Attack on Titan',
            'Saitama': 'One Punch Man',
            'Genos': 'One Punch Man',
            'Tanjiro Kamado': 'Demon Slayer',
            'Nezuko Kamado': 'Demon Slayer',
            'Giyu Tomioka': 'Demon Slayer',
            'Shinobu Kocho': 'Demon Slayer',
            'Kyojuro Rengoku': 'Demon Slayer',
            'Yuji Itadori': 'Jujutsu Kaisen',
            'Megumi Fushiguro': 'Jujutsu Kaisen',
            'Nobara Kugisaki': 'Jujutsu Kaisen',
            'Satoru Gojo': 'Jujutsu Kaisen',
            'Sukuna': 'Jujutsu Kaisen',
            'Makima': 'Chainsaw Man',
            'Denji': 'Chainsaw Man',
            'Power': 'Chainsaw Man',
            'Aki Hayakawa': 'Chainsaw Man',
            'Yor Forger': 'Spy x Family',
            'Loid Forger': 'Spy x Family',
            'Anya Forger': 'Spy x Family',
        }
    
    def normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        if not name:
            return ''
        return re.sub(r'[^\w\s]', '', name.lower()).strip()
    
    def normalize_franchise(self, franchise: str) -> str:
        """Normalize franchise name"""
        if not franchise:
            return ''
        
        # Basic normalization
        normalized = franchise.lower().strip()
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Handle common variations
        variations = {
            'attack on titan': ['shingeki no kyojin', 'aot'],
            'jujutsu kaisen': ['jjk'],
            'demon slayer': ['kimetsu no yaiba'],
            'my hero academia': ['boku no hero academia', 'mha', 'bnha'],
            'hunter x hunter': ['hxh'],
            'one punch man': ['opm'],
            'spy x family': ['spyxfamily'],
        }
        
        for canonical, aliases in variations.items():
            if normalized in aliases or normalized == canonical:
                return canonical
        
        return normalized
    
    def are_same_character(self, char1: Dict, char2: Dict) -> bool:
        """Check if two characters are the same with franchise consideration"""
        name1 = self.normalize_name(char1.get('name', ''))
        name2 = self.normalize_name(char2.get('name', ''))
        
        # Calculate similarity for all cases
        similarity = SequenceMatcher(None, name1, name2).ratio()
        
        # Must have very similar names
        if name1 == name2:
            name_match = True
        else:
            name_match = similarity >= 0.9
        
        if not name_match:
            return False
        
        # Check franchise compatibility
        franchise1 = self.normalize_franchise(char1.get('franchise', ''))
        franchise2 = self.normalize_franchise(char2.get('franchise', ''))
        
        # If both have franchise, they must match
        if franchise1 and franchise2:
            return franchise1 == franchise2
        
        # If one has franchise and the other doesn't, check if we can fix it
        if franchise1 and not franchise2:
            # Check if char2 can get franchise from manual fixes
            fixed_franchise = self.manual_fixes.get(char2.get('name', ''))
            if fixed_franchise:
                return franchise1 == self.normalize_franchise(fixed_franchise)
        
        if franchise2 and not franchise1:
            # Check if char1 can get franchise from manual fixes
            fixed_franchise = self.manual_fixes.get(char1.get('name', ''))
            if fixed_franchise:
                return franchise2 == self.normalize_franchise(fixed_franchise)
        
        # If neither has franchise, only merge if names are very close
        if not franchise1 and not franchise2:
            return similarity >= 0.95
        
        return False
    
    def fix_character_franchise(self, char: Dict) -> Dict:
        """Fix missing franchise information"""
        if not char.get('franchise') or not char['franchise'].strip():
            fixed_franchise = self.manual_fixes.get(char.get('name', ''))
            if fixed_franchise:
                char['franchise'] = fixed_franchise
                print(f"  🔧 Fixed franchise: {char['name']} -> {fixed_franchise}")
        return char
    
    def merge_duplicate_characters(self, chars: List[Dict]) -> Dict:
        """Merge duplicate character entries"""
        if len(chars) == 1:
            return chars[0]
        
        # Choose best character (prefer with franchise, then highest popularity)
        def score_char(char):
            score = char.get('total_popularity_score', 0)
            if char.get('franchise') and char['franchise'].strip():
                score += 1000000
            return score
        
        best_char = max(chars, key=score_char)
        
        # Merge all sources
        all_sources = []
        all_tags = set()
        all_platforms = set()
        total_popularity = 0
        best_rank = float('inf')
        
        for char in chars:
            # Collect sources
            if char.get('sources'):
                all_sources.extend(char['sources'])
            else:
                # Create source from character data
                all_sources.append({
                    'platform': char.get('source', 'unknown'),
                    'rank': char.get('rank'),
                    'popularity_score': char.get('popularity_score', 0),
                    'name_variant': char.get('name'),
                    'franchise': char.get('franchise', ''),
                    'tags': char.get('tags', [])
                })
            
            if char.get('tags'):
                all_tags.update(char['tags'])
            if char.get('platforms'):
                all_platforms.update(char['platforms'])
            
            total_popularity += char.get('total_popularity_score', char.get('popularity_score', 0))
            if char.get('highest_rank') or char.get('rank'):
                rank = char.get('highest_rank') or char.get('rank')
                best_rank = min(best_rank, rank)
        
        # Create merged character
        merged = {
            'name': best_char['name'],
            'franchise': best_char.get('franchise', ''),
            'category': best_char.get('category', ''),
            'description': best_char.get('description', ''),
            'total_popularity_score': total_popularity,
            'highest_rank': best_rank if best_rank != float('inf') else None,
            'source_count': len(all_sources),
            'platforms': sorted(list(all_platforms)) if all_platforms else [s.get('platform') for s in all_sources],
            'tags': sorted(list(all_tags)),
            'sources': all_sources,
            'name_variants': [char['name'] for char in chars],
            'final_rank': 0  # Will be set later
        }
        
        return merged
    
    def clean_data_smart(self, input_file: str, output_file: str):
        """Smart cleaning - only fix obvious issues"""
        print(f"🧠 Smart cleaning data from {input_file}")
        
        # Load data
        characters = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                char = json.loads(line.strip())
                characters.append(char)
        
        print(f"📊 Loaded {len(characters)} characters")
        
        # Step 1: Fix missing franchise info for known characters
        print("🔧 Fixing missing franchise information...")
        fixed_count = 0
        for char in characters:
            original_franchise = char.get('franchise', '')
            char = self.fix_character_franchise(char)
            if char.get('franchise', '') != original_franchise:
                fixed_count += 1
        
        print(f"  ✅ Fixed {fixed_count} franchises")
        
        # Step 2: Only remove characters that definitely have no franchise and can't be fixed
        print("🗑️  Removing unfixable characters without franchise...")
        chars_to_keep = []
        removed_count = 0
        
        for char in characters:
            if char.get('franchise') and char['franchise'].strip():
                chars_to_keep.append(char)
            else:
                # Only remove if we're very sure it's not from anime/game/movie
                name = char.get('name', '')
                # Keep if it might be from a known franchise even if we can't identify it
                if (any(keyword in name.lower() for keyword in ['goku', 'naruto', 'luffy', 'ichigo', 'edward', 'alphonse']) or
                    char.get('category') in ['anime', 'game']):
                    chars_to_keep.append(char)
                    print(f"  ⚠️  Kept without franchise: {name} (might be identifiable)")
                else:
                    removed_count += 1
                    print(f"  ❌ Removed: {name} (no franchise, not identifiable)")
        
        print(f"  🗑️  Removed {removed_count} characters")
        
        # Step 3: Find and merge obvious duplicates
        print("🔗 Merging obvious duplicates...")
        
        # Group by normalized name for initial duplicate detection
        name_groups = defaultdict(list)
        for char in chars_to_keep:
            normalized_name = self.normalize_name(char['name'])
            name_groups[normalized_name].append(char)
        
        merged_characters = []
        merge_count = 0
        
        for normalized_name, group in name_groups.items():
            if len(group) == 1:
                merged_characters.append(group[0])
            else:
                # Check for real duplicates
                duplicate_groups = []
                remaining = group[:]
                
                while remaining:
                    current = remaining.pop(0)
                    duplicates = [current]
                    
                    # Find all characters that are duplicates of current
                    to_remove = []
                    for i, other in enumerate(remaining):
                        if self.are_same_character(current, other):
                            duplicates.append(other)
                            to_remove.append(i)
                    
                    # Remove found duplicates from remaining
                    for i in reversed(to_remove):
                        remaining.pop(i)
                    
                    if len(duplicates) > 1:
                        merged = self.merge_duplicate_characters(duplicates)
                        merged_characters.append(merged)
                        merge_count += 1
                        names = [c['name'] for c in duplicates]
                        print(f"  🔗 Merged: {names}")
                    else:
                        merged_characters.append(duplicates[0])
        
        # Step 4: Sort and rank
        merged_characters.sort(key=lambda x: x.get('total_popularity_score', 0), reverse=True)
        for i, char in enumerate(merged_characters):
            char['final_rank'] = i + 1
        
        # Step 5: Save cleaned data
        print(f"💾 Saving to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            for char in merged_characters:
                f.write(json.dumps(char, ensure_ascii=False) + '\n')
        
        # Statistics
        print(f"\n✅ SMART CLEANING COMPLETE")
        print("=" * 40)
        print(f"📊 Original: {len(characters)}")
        print(f"🔧 Fixed franchises: {fixed_count}")
        print(f"🗑️  Removed: {removed_count}")
        print(f"🔗 Merged duplicates: {merge_count}")
        print(f"🎯 Final: {len(merged_characters)}")
        
        # Show sample of characters with and without franchise
        with_franchise = sum(1 for char in merged_characters if char.get('franchise') and char['franchise'].strip())
        print(f"📚 With franchise: {with_franchise}/{len(merged_characters)} ({with_franchise/len(merged_characters)*100:.1f}%)")
        
        return len(merged_characters)

def main():
    cleaner = SmartDataCleaner()
    
    print("🧠 SMART CHARACTER DATA CLEANER")
    print("=" * 45)
    
    final_count = cleaner.clean_data_smart(
        'final_merged_characters.jsonl',
        'smart_cleaned_characters.jsonl'
    )
    
    print(f"\n🎉 Smart cleaning completed!")
    print(f"📁 Output: smart_cleaned_characters.jsonl")
    print(f"🎯 Final dataset: {final_count} characters")

if __name__ == "__main__":
    main()