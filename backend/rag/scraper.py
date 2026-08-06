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
        "symptoms": ["temperature dropping", "temperature spike", "heater not working", "cold water", "temp swing", "temperature spiked", "temp 84", "84°F", "temperature high"],
        "causes": ["heater failed", "thermostat broken", "power outage", "heater unplugged", "drafts", "heater undersized", "both heaters failed"],
        "treatments": [
            "Check heater is plugged in and functioning properly",
            "Replace heater if malfunctioning immediately",
            "Gradually adjust temperature (max 2°F per hour)",
            "Perform 25% water change with temp-matched water",
            "Check for drafts near tank causing temp drops",
            "Verify thermostat settings are correct (76-80°F)",
            "For temp spikes to 84°F: increase aeration, perform water change",
            "Most corals tolerate 84°F for <12 hours without permanent damage",
            "Install redundant heaters to prevent total failure",
            "Use temperature controller with audible alarm"
        ],
        "references": ["Reef2Reef", "Bulk Reef Supply", "BRS TV", "Reef Central"]
    },
    "salinity_issues": {
        "symptoms": ["salinity high", "specific gravity 1.028", "salinity 1.028", "evaporation", "salinity rising", "sg too high"],
        "causes": ["excessive evaporation", "not topping off", "using saltwater for top-off", "failed ATO", "hot weather increasing evaporation"],
        "treatments": [
            "Gradually lower salinity with RO/DI water over 3-5 days",
            "Target specific gravity 1.025-1.026 (1.024-1.025 for SPS)",
            "Use auto top-off (ATO) system with RO/DI reservoir",
            "Never use saltwater for evaporation replacement",
            "Change 10-15% water with properly mixed saltwater",
            "Monitor salinity daily until stabilized",
            "Check ATO reservoir daily to prevent running dry",
            "Install salinity monitor with audible alarm"
        ],
        "references": ["Bulk Reef Supply", "Reef2Reef", "BRS TV", "Marine Depot"]
    },
    "dosing_pump_clog": {
        "symptoms": ["alkalinity dropping", "low alk", "dosing pump not working", "alk depletion", "alkalinity swinging"],
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
        "symptoms": ["calcium dropping", "low calcium", "slow coral growth", "hollow skeletons", "calcium decline", "bleaching", "calcium at 350"],
        "causes": ["calcium reactor issues", "low calcium in saltwater", "corals consuming calcium", "inadequate supplementation", "reactor media depleted"],
        "treatments": [
            "Test calcium and alkalinity levels",
            "Increase calcium reactor output",
            "Add calcium supplement if needed",
            "Maintain 400-450ppm calcium, 7-9dKH alkalinity",
            "Check calcium reactor media",
            "Consider kalkwasser dosing",
            "Use two-part dosing to raise both Ca and Alk"
        ],
        "references": ["Reef2Reef", "Tampa Bay Reef", "Reef Chemistry 101"]
    },
    "magnesium_spike": {
        "symptoms": ["magnesium high", "magnesium spike", "mg elevated", "magnesium over 1600", "magnesium dropped", "magnesium low", "magnesium 1100", "low mg"],
        "causes": ["overdosing magnesium supplement", "magnesium additive too much", "evaporation concentrating salts", "direct addition error", "magnesium depletion", "corals consuming magnesium"],
        "treatments": [
            "Perform gradual water changes (10-15% daily) with proper salinity",
            "Stop magnesium supplementation immediately if high",
            "Test water for other parameter imbalances (Ca, Alk)",
            "Allow system to stabilize naturally over 1-2 weeks",
            "Do not add more magnesium until levels normalize to 1250-1450ppm",
            "Dose calcium and alkalinity to rebalance relationship",
            "Low magnesium (1100ppm) hurts calcification - raise slowly with supplements",
            "Magnesium must be 3x calcium level for proper coral growth"
        ],
        "references": ["Reef2Reef", "Reef Chemistry 101", "Bulk Reef Supply", "Randy Holmes-Farley"]
    },
    "calcium_alkalinity_balance": {
        "symptoms": ["calcium 350", "low calcium", "alkalinity 6.5", "ca alk imbalance", "calcium high alkalinity low", "cannot raise calcium"],
        "causes": ["imbalanced dosing", "calcium reactor issues", "two-part not mixed correctly", "kalkwasser overdose", "corals consuming faster than dosing"],
        "treatments": [
            "Stop calcium dosing if alk is low (they compete in water)",
            "Two-part dosing: adjust ratio to 1:1 in mmol/L",
            "Target: Ca 400-450ppm, Alk 8-9 dKH, Mg 1250-1450ppm",
            "Raise alkalinity FIRST if both are low (alk drives calcification)",
            "Use Balling method or two-part with proper ratios",
            "Test magnesium - if low (<1200), calcium will not stay stable",
            "Adjust calcium reactor: increase bubble count for more alk, reduce for less alk",
            "Wait 24 hours between adjustments to let parameters stabilize"
        ],
        "references": ["Randy Holmes-Farley", "Reef2Reef Chemistry", "BRS TV Calcium/Alk"]
    },
    "ph_issues": {
        "symptoms": ["ph dropping", "ph too low", "ph swing", "acidosis", "ph below 7.8", "ph drops at night", "ph 7.8", "ph fluctuation", "ph unstable"],
        "causes": ["low alkalinity", "too much CO2", "outgassing", "biological load", "poor ventilation", "old tank water", "lack of aeration", "respiration at night"],
        "treatments": [
            "Increase alkalinity to 8-9 dKH gradually (1 dKH per day)",
            "Check CO2 reactor/producer settings",
            "Improve tank ventilation to remove excess CO2",
            "Reduce feeding to lower bioload",
            "Add Kalkwasser dosing for pH stability",
            "Perform water change with fresh saltwater (pH 8.3)",
            "pH swings of 0.2-0.3 at night are normal due to photosynthesis/respiration cycle",
            "Use a pH controller with CO2 scrubber if swings exceed 0.5",
            "Add aeration with air stone to outgas CO2",
            "Check alkalinity daily - low alk causes pH crashes"
        ],
        "references": ["Reef2Reef", "Reefkeeping.com", "BRS TV", "Randy Holmes-Farley"]
    },
    "alkalinity_stability": {
        "symptoms": ["alkalinity swinging", "alk swings", "alkalinity unstable", "alk between 7 and 9", "alk not stable", "alkalinity fluctuating"],
        "causes": ["inconsistent dosing", "dosing pump issues", "calcium reactor instability", "kalkwasser too strong", "lack of testing", "rapid coral growth consuming alk"],
        "treatments": [
            "Test alkalinity daily at same time to track trends",
            "Use a dosing pump for consistent 24-hour delivery",
            "Set dosing pump to small, frequent doses (6x per day)",
            "Target stable alkalinity within 0.5 dKH variation",
            "If using calcium reactor, adjust bubble count and effluent rate slowly",
            "Stop kalkwasser if pH exceeds 8.4",
            "Two-part dosing is more stable than single supplements",
            "Check calcium reactor media and effluent pH (target 6.5-6.8)",
            "Consider a dosing controller with pH probe feedback loop"
        ],
        "references": ["BRS TV Alkalinity", "Reef2Reef Stability", "Randy Holmes-Farley"]
    },
    "nitrate_issues": {
        "symptoms": ["nitrate high", "nitrates elevated", "algae growth", "nitrate above 20ppm", "hairy algae", "brown slime"],
        "causes": ["overfeeding", "insufficient filtration", "dead spots", "inadequate protein skimming", "lack of export"],
        "treatments": [
            "Reduce feeding by 50%",
            "Increase protein skimmer operation",
            "Add or improve mechanical filtration",
            "Consider GAC (granular activated carbon)",
            "Water change 25%",
            "Add more clean-up crew",
            "Use nitrate-reducing media or refugium"
        ],
        "references": ["Reef2Reef", "Marine Depot"]
    },
    "phosphate_issues": {
        "symptoms": ["phosphate high", "phosphates elevated", "algae outbreak", "po4 above 0.1ppm", "bubble algae", "cyanobacteria"],
        "causes": ["overfeeding", "dirty filters", "tap water with phosphate", "overstocking", "decaying organic matter"],
        "treatments": [
            "Reduce feeding",
            "Clean or replace filter media",
            "Use RO/DI water for top-offs",
            "Add phosphate remover",
            "Increase water flow",
            "Remove visible algae manually",
            "Run GFO (granular ferric oxide)"
        ],
        "references": ["Reef2Reef", "Bulk Reef Supply"]
    },
    "coral_bleaching": {
        "symptoms": ["coral bleaching", "turning white", "coral pale", "coral closed", "not opening", "acropora bleaching", "coral tissue loss", "coral turning white", "lps bleaching", "sps bleaching"],
        "causes": ["high temperature", "low pH", "poor lighting", "unstable parameters", "new tank syndrome", "low alkalinity", "low calcium", "high nitrates", "lack of flow"],
        "treatments": [
            "Check alkalinity (8-9 dKH), calcium (400-450ppm), magnesium (1250-1450ppm)",
            "Verify temperature is stable 76-80°F",
            "Check lighting PAR levels (150-250 for SPS, 50-150 for LPS)",
            "Test ammonia and nitrite (should be 0 in established tank)",
            "Perform 10-15% water change with matched parameters",
            "Ensure adequate water flow around coral",
            "New tanks need 4-6 weeks to fully cycle before adding corals",
            "Check for pests like Acro-eating flatworms or nudibranchs",
            "Reduce lighting intensity if corals are pale or bleached"
        ],
        "references": ["Reef2Reef", "BRS TV", "Tampa Bay Reef", "Reefkeeping Magazine"]
    },
    "torch_coral_care": {
        "symptoms": ["torch coral tentacles not coming out", "torch coral deflated", "torch coral not opening", "euphyllia closed", "torch coral tentacles short", "torch not extending"],
        "causes": ["too much flow", "insufficient lighting", "poor water quality", "neighboring coral stinging", "sweeper tentacles", "low alkalinity", "transport stress"],
        "treatments": [
            "Ensure moderate water flow (10-20 GPH), not too strong",
            "Provide low to moderate lighting (50-100 PAR)",
            "Check alkalinity (8-9 dKH), calcium (400-450ppm), magnesium (1250-1450ppm)",
            "Move away from other Euphyllia corals (they sting each other)",
            "Check for sweeper tentacles from nearby corals at night",
            "Test nitrates (<10ppm) and phosphates (<0.1ppm)",
            "Give coral 1-2 weeks to adjust after placement",
            "Perform 10-15% water change if parameters are off"
        ],
        "references": ["Reef2Reef Torch Coral", "BRS TV LPS Care", "Euphyllia Guide"]
    },
    "fish_disease": {
        "symptoms": ["flashing", "scratching", "ich", "white spots", "velvet", "brooklynella", "scratching against rocks"],
        "causes": ["parasites", "poor water quality", "stress", "new fish introduction"],
        "treatments": [
            "Quarantine affected fish immediately",
            "Treat with Ich-X or formalin for ich",
            "Use MetroPlex for velvet and brooklynella",
            "Check ammonia, nitrite, nitrate levels",
            "Maintain stable temperature and salinity",
            "Consider copper treatment in quarantine tank"
        ],
        "references": ["Reef2Reef", "Humane Fish", "Reef2Reef Disease Forum"]
    },
    "salinity_issues": {
        "symptoms": ["salinity high", "specific gravity 1.028", "salinity 1.028", "evaporation"],
        "causes": ["excessive evaporation", "not topping off", "using saltwater for top-off"],
        "treatments": [
            "Gradually lower salinity with RO/DI water",
            "Target specific gravity 1.025-1.026",
            "Use auto top-off (ATO) system",
            "Never use saltwater for evaporation replacement",
            "Change 10-15% water with proper salinity",
            "Monitor salinity daily until stabilized"
        ],
        "references": ["Bulk Reef Supply", "Reef2Reef", "BRS TV"]
    },
    "coral_pests": {
        "symptoms": ["red bugs", "acro-eating flatworms", "acropora red bugs", "flatworms on coral"],
        "causes": ["introduction on new corals", "no quarantine", "pest hitchhikers"],
        "treatments": [
            "Dip coral in coral dip solution (Coral Rx)",
            "Treat with Interceptor (milbemycin) for red bugs",
            "Manual removal with soft toothbrush",
            "Quarantine coral to prevent spread",
            "Consider flatworm exit for flatworm infestations"
        ],
        "references": ["Reef2Reef", "BRS TV", "AEFW Guide"]
    },
    "algae_outbreak": {
        "symptoms": ["hair algae", "long hairy algae", "bubble algae", "green algae taking over", "algae growing rapidly"],
        "causes": ["high nitrates", "high phosphates", "excess nutrients", "too much light", "poor nutrient export"],
        "treatments": [
            "Test and lower nitrates (<10ppm) and phosphates (<0.1ppm)",
            "Increase water changes to 10-15% weekly",
            "Add herbivores (tangs, snails, emerald crabs)",
            "Use phosphate remover (GFO)",
            "Reduce lighting duration or intensity",
            "Manual algae removal with siphon",
            "Consider refugium for nutrient export"
        ],
        "references": ["Reef2Reef", "Bulk Reef Supply", "BRS TV Algae"]
    },
    "cyanobacteria": {
        "symptoms": ["brown slime", "cyano", "cyanobacteria", "red slime", "sandbed covered"],
        "causes": ["high nutrients", "poor flow", "old substrate", "low oxygen"],
        "treatments": [
            "Improve water flow in affected areas",
            "Reduce nitrates and phosphates",
            "Siphon out cyanobacteria manually",
            "Use chemiclean or similar treatment",
            "Increase protein skimming",
            "Consider GAC and phosphate removal"
        ],
        "references": ["Reef2Reef", "Marine Depot", "BRS TV"]
    },
    "amino_acid_toxicity": {
        "symptoms": ["mushrooms turning white", "mushrooms melting", "mushrooms bleaching", "soft coral pale", "ricordea melting", "corallimorphs dying"],
        "causes": ["excessive amino acid dosing", "aminos overdosed", "acropower toxicity"],
        "treatments": [
            "Stop dosing amino acids immediately",
            "Perform a 20% water change to dilute aminos",
            "Run fresh activated carbon",
            "Do not dip corals, as it will stress them further",
            "Wait for zooxanthellae to naturally repopulate the tissue"
        ],
        "references": ["Reef2Reef", "Bulk Reef Supply", "Coral Magazine"]
    },
    "clam_health": {
        "symptoms": ["clam not extending mantle", "clam pale", "clam closed", "mantle retraction", "clam not opening"],
        "causes": ["insufficient lighting", "poor water quality", "low alkalinity", "low calcium", "acclimation stress", "lack of phytoplankton"],
        "treatments": [
            "Ensure adequate lighting (high PAR for clams, 200-300)",
            "Test alkalinity (8-9 dKH), calcium (400-450ppm), nitrates (<10ppm)",
            "Provide phytoplankton feeding 2-3x per week",
            "Check water flow (moderate, not too high directly on clam)",
            "Maintain stable temperature 76-80°F",
            "Perform water change if parameters are off",
            "Give new clams 1-2 weeks to acclimate to lighting"
        ],
        "references": ["Reef2Reef", "Clam Care Guide", "BRS TV", "Tridacna Guide"]
    },
    "lighting_issues": {
        "symptoms": ["coral pale", "coral bleaching", "coral closed", "SPS turning white", "too much light", "coral colors fading"],
        "causes": ["lighting too intense", "too many hours", "new bulbs/lEDs", "PAR too high", "acclimation too fast"],
        "treatments": [
            "Reduce lighting intensity by 20-30% if SPS bleaching",
            "Shorten photoperiod to 8-9 hours initially",
            "Acclimate new corals gradually over 2-3 weeks",
            "Target PAR: 150-250 for SPS, 50-150 for LPS, 30-80 for softies",
            "Raise lights higher above water surface to reduce intensity",
            "Add shade cloth or screen to reduce PAR by 25-50%",
            "Observe coral response over 5-7 days before further changes"
        ],
        "references": ["BRS TV Lighting", "Reef2Reef PAR", "Ecotinic LED Guide"]
    },
    "water_flow_issues": {
        "symptoms": ["coral closed", "cyano in spots", "detritus buildup", "algae in corners", "dead spots"],
        "causes": ["insufficient flow", "poor circulation", "dead spots", "powerhead failed", "too much flow for coral"],
        "treatments": [
            "Increase flow to 10-20x tank volume turnover per hour",
            "Add or reposition powerheads to eliminate dead spots",
            "Target flow: 20-30 GPH per watt for SPS, 10-15 for LPS",
            "Use wavemakers or alternating flow patterns",
            "Clean powerhead intakes if flow reduced",
            "Reduce direct flow on LPS corals (they prefer gentle flow)",
            "Add circulation pump if flow is <5x tank volume per hour"
        ],
        "references": ["Reef2Reef Flow", "BRS TV Flow", "Ecotech Vortech Guide"]
    },
    "new_tank_syndrome": {
        "symptoms": ["all corals closed", "corals not opening", "new tank", "cycling", "corals stressed", "tank 2 weeks old"],
        "causes": ["tank not fully cycled", "ammonia present", "nitrite present", "unstable parameters", "new system", "lack of beneficial bacteria"],
        "treatments": [
            "Test ammonia and nitrite (should be 0 ppm in cycled tank)",
            "Perform 10-15% water change with matched parameters",
            "Wait 4-6 weeks for tank to fully cycle before adding sensitive corals",
            "Add beneficial bacteria supplements to boost cycle",
            "Keep lighting low (6-8 hours) until tank stabilizes",
            "Don't add more livestock until parameters are stable",
            "Test pH, alkalinity, calcium every 2-3 days",
            "Be patient - new tanks need time to mature biologically"
        ],
        "references": ["Reef2Reef New Tank", "BRS TV Beginner", "Tampa Bay Cycle Guide"]
    },
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