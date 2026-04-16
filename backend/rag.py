"""
RAG Knowledge Base for Reef Keeping
Scrapes and indexes reef keeping information for clinical diagnostics.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional

# Local knowledge base - in production, this would use embeddings + vector DB
KNOWLEDGE_BASE = {
    "heater_malfunction": {
        "symptoms": ["temperature dropping", "temperature spike", "heater not working", "cold water", "temp swing"],
        "causes": ["heater failed", "thermostat broken", "power outage", "heater unplugged"],
        "treatments": [
            "Check heater is plugged in and functioning",
            "Replace heater if malfunctioning",
            "Gradually adjust temperature (max 2°F per hour)",
            "Perform 25% water change with temp-matched water",
            "Check for drafts near tank"
        ],
        "references": ["Reef2Reef", "ReefKeeping Magazine"]
    },
    "dosing_pump_clog": {
        "symptoms": ["alkalinity dropping", "low alk", "dosing pump not working", "alk depletion"],
        "causes": ["dosing pump clogged", "dosing bottle empty", "air lock in tubing", "pump malfunction"],
        "treatments": [
            "Check dosing pump is working",
            "Clear any clogs in tubing",
            "Refill dosing containers",
            "Prime the dosing lines",
            "Manual dose alkalinity to recover"
        ],
        "references": ["Reef2Reef", "Bulk Reef Supply"]
    },
    "calcifier_depletion": {
        "symptoms": ["calcium dropping", "low calcium", "slow coral growth", "hollow skeletons", "calcium decline"],
        "causes": ["calcium reactor issues", "low calcium in saltwater", "corals consuming calcium", "inadequate supplementation"],
        "treatments": [
            "Test calcium and alkalinity levels",
            "Increase calcium reactor output",
            "Add calcium supplement if needed",
            "Maintain 400-450ppm calcium, 7-9dKH alkalinity",
            "Check for coral bleaching indicating depletion"
        ],
        "references": ["Reef2Reef", "Tampa Bay Reef"]
    },
    "magnesium_spike": {
        "symptoms": ["magnesium high", "magnesium spike", "mg elevated"],
        "causes": ["overdosing magnesium supplement", "magnesium additive too much", "evaporation concentrating salts"],
        "treatments": [
            "Perform gradual water change (10-15% daily)",
            "Stop magnesium supplementation",
            "Test water for other parameter imbalances",
            "Allow system to stabilize naturally",
            "Do not add more magnesium until levels normalize"
        ],
        "references": ["Reef2Reef", "Reef Chemistry 101"]
    },
    "ph_issues": {
        "symptoms": ["ph dropping", "ph too low", "ph swing", "acidosis", "ph波动"],
        "causes": ["low alkalinity", "too much CO2", "outgassing", "biological load", "poor ventilation"],
        "treatments": [
            "Increase alkalinity to 8-9dKH",
            "Check CO2 reactor/producer",
            "Improve tank ventilation",
            "Reduce feeding",
            "Add Kalkwasser dosing for stability"
        ],
        "references": ["Reef2Reef", "Reefkeeping.com"]
    },
    "general_maintenance": {
        "symptoms": [],
        "causes": [],
        "treatments": [
            "Test water parameters weekly",
            "25% water change monthly",
            "Clean protein skimmer cup",
            "Check flow pump performance",
            "Inspect heater and cooling",
            "Monitor dosing pump operation"
        ],
        "references": ["Reef2Reef", "BRS TV"]
    }
}


def get_diagnosis_context(warning_parameters: List[str], current_values: Dict) -> str:
    """Generate context for ReefGPT based on warning parameters and current values."""
    if not warning_parameters:
        context = KNOWN_ISSUES.get("general_maintenance", {})
        return format_context("general_maintenance", context)
    
    issues = []
    for param in warning_parameters:
        issue_key = _map_param_to_issue(param, current_values)
        if issue_key and issue_key in KNOWN_ISSUES:
            issues.append(issue_key)
    
    context_parts = []
    for issue in issues:
        context_parts.append(format_context(issue, KNOWN_ISSUES[issue]))
    
    return "\n\n".join(context_parts) if context_parts else format_context("general_maintenance", KNOWN_ISSUES["general_maintenance"])


def _map_param_to_issue(param: str, values: Dict) -> Optional[str]:
    """Map a parameter to the likely issue based on values."""
    param = param.lower() if param else ""
    
    # Temperature issues
    if param == "temperature":
        temp = values.get("Temperature", 0)
        if temp < 76:
            return "heater_malfunction"
        if temp > 82:
            return "temperature_spike"
    
    # Alkalinity issues
    if param in ["alkalinity", "alk"]:
        alk = values.get("Alkalinity", 0)
        if alk < 7.5:
            return "dosing_pump_clog"
        if alk > 11:
            return "alkalinity_excess"
    
    # Calcium issues
    if param == "calcium":
        ca = values.get("Calcium", 0)
        if ca < 380:
            return "calcifier_depletion"
    
    # pH issues
    if param == "ph":
        ph = values.get("pH", 0)
        if ph < 7.8:
            return "ph_issues"
    
    # Magnesium issues
    if param == "magnesium":
        mg = values.get("Magnesium", 0)
        if mg > 1500:
            return "magnesium_spike"
        if mg < 1200:
            return "magnesium_depletion"
    
    return None


def format_context(issue_key: str, issue_data: Dict) -> str:
    """Format issue data into readable context."""
    lines = [f"## {issue_key.replace('_', ' ').title()}"]
    
    if issue_data.get("symptoms"):
        lines.append("### Symptoms:")
        for s in issue_data["symptoms"]:
            lines.append(f"- {s}")
    
    if issue_data.get("causes"):
        lines.append("### Possible Causes:")
        for c in issue_data["causes"]:
            lines.append(f"- {c}")
    
    if issue_data.get("treatments"):
        lines.append("### Recommended Actions:")
        for t in issue_data["treatments"]:
            lines.append(f"- {t}")
    
    if issue_data.get("references"):
        lines.append(f"### References: {', '.join(issue_data['references'])}")
    
    return "\n".join(lines)


# Alias for compatibility
KNOWN_ISSUES = KNOWLEDGE_BASE


def get_reef_advice(param: str, value: float) -> Dict:
    """Get specific advice for a parameter value."""
    param = param.lower() if param else ""
    
    advice = {
        "Alkalinity": {
            "low": {"message": "Alkalinity is low. Check dosing pump operation and consider adding buffer.", "severity": "warning"},
            "high": {"message": "Alkalinity is elevated. Perform water change to reduce.", "severity": "warning"},
            "critical": {"message": "Alkalinity critical! Immediate water change recommended.", "severity": "critical"}
        },
        "Calcium": {
            "low": {"message": "Calcium depleted. Increase calcium reactor or supplement.", "severity": "warning"},
            "high": {"message": "Calcium elevated. Check water change schedule.", "severity": "warning"},
            "critical": {"message": "Calcium critically low - coral health at risk!", "severity": "critical"}
        },
        "Magnesium": {
            "low": {"message": "Magnesium low. Add magnesium supplement.", "severity": "warning"},
            "high": {"message": "Magnesium elevated. Perform gradual water changes.", "severity": "warning"},
            "critical": {"message": "Magnesium severely imbalanced!", "severity": "critical"}
        },
        "pH": {
            "low": {"message": "pH low. Check CO2 levels and improve ventilation.", "severity": "warning"},
            "high": {"message": "pH high. Check for alkalinity issues.", "severity": "warning"},
            "critical": {"message": "pH outside safe range! Test immediately.", "severity": "critical"}
        },
        "Temperature": {
            "low": {"message": "Temperature low. Check heater operation.", "severity": "warning"},
            "high": {"message": "Temperature high. Check chiller and room temp.", "severity": "warning"},
            "critical": {"message": "Temperature critical! Coral stress imminent.", "severity": "critical"}
        }
    }
    
    # Get the appropriate advice
    if param in advice:
        value_key = "low" if value < 0 else "high"  # Simplified
        return advice[param].get(value_key, {"message": "Monitor parameter", "severity": "info"})
    
    return {"message": "No specific advice", "severity": "info"}


if __name__ == "__main__":
    # Test the RAG system
    print("Testing Knowledge Base:")
    print(get_diagnosis_context(["Temperature", "Alkalinity"], {"Temperature": 72, "Alkalinity": 6.0}))
    print("\n" + "="*50)
    print(get_reef_advice("Temperature", 72))