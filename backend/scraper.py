"""
Reef Knowledge Base - Alternative Sources
Uses publicly available reef-keeping resources.
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict

# Alternative public sources
PUBLIC_SOURCES = {
    "bulk_reef_supply_blog": "https://www.bulkreefsupply.com/blog/feed/",
    "tropical_fish": "https://www.thesprucepets.com/feed",
}

# Pre-curated knowledge from common reef issues
MANUAL_KNOWLEDGE = {
    "heater_malfunction": {
        "symptoms": ["temperature dropping", "temperature spike", "heater not working", "cold water", "temp swing"],
        "causes": ["heater failed", "thermostat broken", "power outage", "heater unplugged", "drafts"],
        "treatments": [
            "Check heater is plugged in and functioning",
            "Replace heater if malfunctioning",
            "Gradually adjust temperature (max 2°F per hour)",
            "Perform 25% water change with temp-matched water",
            "Check for drafts near tank",
            "Verify thermostat settings"
        ],
        "references": ["Reef2Reef", "Bulk Reef Supply", "BRS TV"]
    },
    "dosing_pump_clog": {
        "symptoms": ["alkalinity dropping", "low alk", "dosing pump not working", "alk depletion"],
        "causes": ["dosing pump clogged", "dosing bottle empty", "air lock in tubing", "pump malfunction", "tubing disconnection"],
        "treatments": [
            "Check dosing pump is working and powered",
            "Clear any clogs in tubing",
            "Refill dosing containers",
            "Prime the dosing lines by running pump manually",
            "Manual dose alkalinity to recover levels",
            "Check for air bubbles in tubing"
        ],
        "references": ["Reef2Reef", "Bulk Reef Supply", "Reefer.com"]
    },
    "calcifier_depletion": {
        "symptoms": ["calcium dropping", "low calcium", "slow coral growth", "hollow skeletons", "calcium decline", " bleaching"],
        "causes": ["calcium reactor issues", "low calcium in saltwater", "corals consuming calcium", "inadequate supplementation", "reactor media depleted"],
        "treatments": [
            "Test calcium and alkalinity levels",
            "Increase calcium reactor output",
            "Add calcium supplement if needed",
            "Maintain 400-450ppm calcium, 7-9dKH alkalinity",
            "Check calcium reactor media",
            "Consider kalkwasser dosing"
        ],
        "references": ["Reef2Reef", "Tampa Bay Reef", "Reef Chemistry 101"]
    },
    "magnesium_spike": {
        "symptoms": ["magnesium high", "magnesium spike", "mg elevated", "magnesium over 1600"],
        "causes": ["overdosing magnesium supplement", "magnesium additive too much", "evaporation concentrating salts", "direct addition error"],
        "treatments": [
            "Perform gradual water changes (10-15% daily)",
            "Stop magnesium supplementation immediately",
            "Test water for other parameter imbalances",
            "Allow system to stabilize naturally over 1-2 weeks",
            "Do not add more magnesium until levels normalize to 1250-1450ppm"
        ],
        "references": ["Reef2Reef", "Reef Chemistry 101", "Bulk Reef Supply"]
    },
    "ph_issues": {
        "symptoms": ["ph dropping", "ph too low", "ph swing", "acidosis", "ph below 7.8"],
        "causes": ["low alkalinity", "too much CO2", "outgassing", "biological load", "poor ventilation", "old tank water"],
        "treatments": [
            "Increase alkalinity to 8-9dKH gradually",
            "Check CO2 reactor/producer settings",
            "Improve tank ventilation",
            "Reduce feeding to lower bioload",
            "Add Kalkwasser dosing for stability",
            "Perform water change with fresh saltwater"
        ],
        "references": ["Reef2Reef", "Reefkeeping.com", "BRS TV"]
    },
    "nitrate_issues": {
        "symptoms": ["nitrate high", "nitrates elevated", "algae growth", "nitrate above 20ppm"],
        "causes": ["overfeeding", "insufficient filtration", "dead spots", "inadequate protein skimming", "lack of export"],
        "treatments": [
            "Reduce feeding by 50%",
            "Increase protein skimmer operation",
            "Add or improve mechanical filtration",
            "Consider GAC (granular activated carbon)",
            "Water change 25%",
            "Add more fish or cleanup crew"
        ],
        "references": ["Reef2Reef", "Marine Depot"]
    },
    "phosphate_issues": {
        "symptoms": ["phosphate high", "phosphates elevated", "algae outbreak", "po4 above 0.1ppm"],
        "causes": ["overfeeding", "dirty filters", "tap water with phosphate", "overstocking", "decaying organic matter"],
        "treatments": [
            "Reduce feeding",
            "Clean or replace filter media",
            "Use RO/DI water for top-offs",
            "Add phosphate remover",
            "Increase water flow",
            "Remove visible algae manually"
        ],
        "references": ["Reef2Reef", "Bulk Reef Supply"]
    }
}


class ReefKnowledgeCollector:
    """Collects reef-keeping knowledge from multiple sources."""
    
    def __init__(self, cache_file: str = "knowledge_cache.json"):
        self.cache_file = cache_file
        self.knowledge = {}
        self.load_cache()
    
    def load_cache(self):
        """Load cached knowledge."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.knowledge = json.load(f)
            except:
                self.knowledge = {}
    
    def save_cache(self):
        """Save knowledge to cache."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.knowledge, f, indent=2)
    
    def fetch_url(self, url: str) -> List[Dict]:
        """Try to fetch from URL (handles blocks gracefully)."""
        try:
            headers = {'User-Agent': 'ReefOS/1.0'}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return [{"title": "Fetched data", "content": response.text[:500], "source": url}]
        except:
            pass
        return []
    
    def initialize_from_manual(self):
        """Initialize with pre-curated knowledge."""
        self.knowledge = MANUAL_KNOWLEDGE
        self.save_cache()
        print(f"Loaded {len(MANUAL_KNOWLEDGE)} pre-curated knowledge entries")
    
    def get_issue_info(self, issue: str) -> Dict:
        """Get full info for an issue."""
        if not self.knowledge:
            self.initialize_from_manual()
        
        return self.knowledge.get(issue, {})
    
    def get_treatment_for_issue(self, issue: str) -> List[str]:
        """Get treatments for specific issue."""
        info = self.get_issue_info(issue)
        return info.get("treatments", [])
    
    def get_related_issues(self, param: str, value: float) -> List[str]:
        """Map parameter to related issues."""
        issues = []
        
        param_lower = param.lower()
        
        if param_lower in ['temperature', 'temp']:
            if value < 76:
                issues.append('heater_malfunction')
            elif value > 82:
                issues.append('heater_malfunction')
        
        if param_lower in ['alkalinity', 'alk']:
            if value < 7.5:
                issues.append('dosing_pump_clog')
            elif value > 11:
                issues.append('ph_issues')
        
        if param_lower == 'calcium':
            if value < 380:
                issues.append('calcifier_depletion')
        
        if param_lower == 'magnesium':
            if value > 1500:
                issues.append('magnesium_spike')
            elif value < 1200:
                issues.append('magnesium_spike')  # Could add separate depletion
        
        if param_lower == 'ph':
            if value < 7.8 or value > 8.6:
                issues.append('ph_issues')
        
        return issues
    
    def get_recommendation_context(self, warnings: List[str], current_values: Dict) -> str:
        """Generate context for ReefGPT from warnings."""
        if not self.knowledge:
            self.initialize_from_manual()
        
        context_parts = []
        
        for param in warnings:
            related = self.get_related_issues(param, current_values.get(param, 0))
            for issue in related:
                info = self.knowledge.get(issue, {})
                if info:
                    context_parts.append(f"## {issue.replace('_', ' ').title()}")
                    if info.get('treatments'):
                        context_parts.append("Recommended actions:")
                        for t in info['treatments'][:3]:
                            context_parts.append(f"- {t}")
                    if info.get('references'):
                        context_parts.append(f"References: {', '.join(info['references'])}")
        
        return '\n'.join(context_parts) if context_parts else ""


def get_recommendation_system():
    """Get the recommendation system singleton."""
    return ReefKnowledgeCollector()


if __name__ == "__main__":
    collector = ReefKnowledgeCollector()
    collector.initialize_from_manual()
    
    print("Knowledge Base Loaded:")
    for issue, info in MANUAL_KNOWLEDGE.items():
        print(f"  - {issue}: {len(info.get('treatments', []))} treatments")
    
    # Test
    print("\nTest - Calcium depletion:")
    print(collector.get_issue_info('calcifier_depletion'))