#!/usr/bin/env python3
"""
Smart Account Matching System
Matches Excel account names to dropdown options with fuzzy matching
"""

import json
import re
from difflib import SequenceMatcher
from typing import List, Dict, Tuple, Optional

class AccountMatcher:
    def __init__(self, dropdown_accounts_file: str = "dropdown_accounts.json"):
        """Initialize matcher with dropdown accounts"""
        with open(dropdown_accounts_file, 'r') as f:
            data = json.load(f)
            self.dropdown_accounts = [(acc["value"], acc["name"]) for acc in data["accounts"]]

        print(f"Loaded {len(self.dropdown_accounts)} dropdown accounts")

    def clean_name(self, name: str) -> str:
        """Clean and normalize account name for matching"""
        # Remove extra spaces, convert to lowercase
        cleaned = re.sub(r'\s+', ' ', name.strip().lower())

        # Remove common prefixes like "4141 -"
        cleaned = re.sub(r'^4141\s*-\s*', '', cleaned)

        return cleaned

    def extract_business_name(self, name: str) -> str:
        """Extract business name from Excel format (before contact person)"""
        # Split on dash and take first part (business name)
        parts = name.split(' - ')
        business_name = parts[0].strip()

        # Clean the business name
        return self.clean_name(business_name)

    def similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings (0.0 to 1.0)"""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def match_account(self, excel_name: str, confidence_threshold: float = 0.8) -> Dict:
        """
        Match an Excel account name to dropdown options

        Args:
            excel_name: Name from Excel (e.g., "CSLL - John Smith")
            confidence_threshold: Minimum confidence for automatic match

        Returns:
            Dictionary with match results
        """
        business_name = self.extract_business_name(excel_name)

        # Try different matching strategies
        matches = []

        # Strategy 1: Exact substring match
        for value, dropdown_name in self.dropdown_accounts:
            dropdown_clean = self.clean_name(dropdown_name)

            # Check if business name appears in dropdown name
            if business_name in dropdown_clean or dropdown_clean in business_name:
                similarity_score = self.similarity(business_name, dropdown_clean)
                matches.append({
                    "strategy": "exact_substring",
                    "value": value,
                    "dropdown_name": dropdown_name,
                    "confidence": min(1.0, similarity_score * 1.2)  # Boost exact matches
                })

        # Strategy 2: Fuzzy matching for all accounts
        for value, dropdown_name in self.dropdown_accounts:
            dropdown_clean = self.clean_name(dropdown_name)
            similarity_score = self.similarity(business_name, dropdown_clean)

            if similarity_score >= 0.6:  # Only consider reasonable matches
                matches.append({
                    "strategy": "fuzzy_match",
                    "value": value,
                    "dropdown_name": dropdown_name,
                    "confidence": similarity_score
                })

        # Remove duplicates and sort by confidence
        unique_matches = {}
        for match in matches:
            key = match["value"]
            if key not in unique_matches or match["confidence"] > unique_matches[key]["confidence"]:
                unique_matches[key] = match

        sorted_matches = sorted(unique_matches.values(), key=lambda x: x["confidence"], reverse=True)

        # Return result
        result = {
            "excel_name": excel_name,
            "business_name": business_name,
            "matches": sorted_matches[:5],  # Top 5 matches
            "auto_match": None,
            "status": "no_match"
        }

        if sorted_matches:
            best_match = sorted_matches[0]
            result["auto_match"] = best_match

            if best_match["confidence"] >= confidence_threshold:
                result["status"] = "confident_match"
            elif best_match["confidence"] >= 0.7:
                result["status"] = "probable_match"
            else:
                result["status"] = "uncertain_match"

        return result

    def match_excel_list(self, excel_accounts: List[str], confidence_threshold: float = 0.8) -> Dict:
        """Match a list of Excel account names"""
        results = {
            "confident_matches": [],
            "probable_matches": [],
            "uncertain_matches": [],
            "no_matches": [],
            "summary": {}
        }

        for excel_name in excel_accounts:
            match_result = self.match_account(excel_name, confidence_threshold)

            if match_result["status"] == "confident_match":
                results["confident_matches"].append(match_result)
            elif match_result["status"] == "probable_match":
                results["probable_matches"].append(match_result)
            elif match_result["status"] == "uncertain_match":
                results["uncertain_matches"].append(match_result)
            else:
                results["no_matches"].append(match_result)

        # Summary statistics
        total = len(excel_accounts)
        results["summary"] = {
            "total_accounts": total,
            "confident_matches": len(results["confident_matches"]),
            "probable_matches": len(results["probable_matches"]),
            "uncertain_matches": len(results["uncertain_matches"]),
            "no_matches": len(results["no_matches"]),
            "auto_processable": len(results["confident_matches"]) + len(results["probable_matches"])
        }

        return results

    def save_results(self, results: Dict, filename: str = "account_matching_results.json"):
        """Save matching results to file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {filename}")

def test_matcher():
    """Test the matcher with sample data"""
    print("Testing Account Matcher...")

    matcher = AccountMatcher()

    # Test with sample names
    test_names = [
        "CSLL - John Smith",
        "Dell Anno - Maria Garcia",
        "Design Within Reach - David Wilson",
        "B&B Italia - Sarah Johnson",
        "Christies - Michael Brown",
        "Some Unknown Company - Jane Doe"
    ]

    print(f"\nTesting with {len(test_names)} sample accounts:")

    for name in test_names:
        result = matcher.match_account(name)
        print(f"\n'{name}':")
        print(f"  Status: {result['status']}")
        if result['auto_match']:
            print(f"  Best match: {result['auto_match']['dropdown_name']}")
            print(f"  Confidence: {result['auto_match']['confidence']:.2f}")
        else:
            print("  No matches found")

if __name__ == "__main__":
    test_matcher()