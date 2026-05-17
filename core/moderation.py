"""
Content Moderation Module
Filters products for profanity, inappropriate content before marketplace posting.
"""

import re
import logging
from pathlib import Path
from typing import List, Set

logger = logging.getLogger(__name__)


class ContentModerator:
    """Moderates product listings for marketplace compliance"""
    
    def __init__(self, profanity_file_path: str = None):
        self.profanity_words: Set[str] = set()
        
        # Load custom profanity list if provided
        if profanity_file_path and Path(profanity_file_path).exists():
            self._load_profanity_list(profanity_file_path)
        
        # Add common marketplace-prohibited terms
        self.marketplace_prohibited = {
            "counterfeit", "fake", "replica", "knockoff",
            "pirated", "bootleg", "stolen", "used as new"
        }
        
    def _load_profanity_list(self, file_path: str):
        """Load custom profanity words from file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().lower()
                if line and not line.startswith('#'):
                    self.profanity_words.add(line)
        
        logger.info(f"Loaded {len(self.profanity_words)} profanity words")
    
    def check_title(self, title: str) -> dict:
        """Check product title for issues"""
        issues = []
        title_lower = title.lower()
        
        # Check for profanity
        for word in self.profanity_words:
            if word in title_lower:
                issues.append(f"Profanity detected: '{word}'")
        
        # Check for prohibited terms
        for term in self.marketplace_prohibited:
            if term in title_lower:
                issues.append(f"Prohibited term: '{term}' (marketplaces ban counterfeit claims)")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "severity": "high" if any("Prohibited" in i for i in issues) else "medium"
        }
    
    def check_description(self, description: str) -> dict:
        """Check product description for issues"""
        issues = []
        
        # Check for profanity
        for word in self.profanity_words:
            if re.search(rf'\b{word}\b', description.lower()):
                issues.append(f"Profanity detected: '{word}'")
        
        # Check for prohibited claims
        prohibited_claims = [
            r"authentic\.*guaranteed",  # Fake authenticity claims
            r"100%\s*real",             # Overly absolute claims
            r"never\s*bought\.*used",   # False usage claims
        ]
        
        for pattern in prohibited_claims:
            if re.search(pattern, description.lower()):
                issues.append(f"Suspicious claim matching pattern: {pattern}")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "severity": "high" if any("Prohibited" in i for i in issues) else "medium"
        }
    
    def check_all(self, title: str, description: str) -> dict:
        """Run full moderation check"""
        title_check = self.check_title(title)
        desc_check = self.check_description(description)
        
        all_passed = title_check["passed"] and desc_check["passed"]
        
        # Determine overall severity
        if title_check["severity"] == "high" or desc_check["severity"] == "high":
            severity = "high"
        elif title_check["severity"] == "medium" or desc_check["severity"] == "medium":
            severity = "medium"
        else:
            severity = "low"
        
        return {
            "passed": all_passed,
            "title": title_check,
            "description": desc_check,
            "overall_severity": severity,
            "needs_review": not all_passed or severity == "high",
            "flags": title_check["issues"] + desc_check["issues"]
        }


def create_moderator(config: dict) -> ContentModerator:
    """Factory function"""
    profanity_file = config.get("profanity_file")
    return ContentModerator(profanity_file_path=profanity_file)
