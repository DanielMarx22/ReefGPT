"""
RAG Diagnostic Router for ReefGPT
Analyzes the prompt to apply Generalized Expert Data Science Rules
before the LLM generates a response.
"""

from typing import List, Dict

def get_expert_routing_rules(query: str) -> str:
    """
    Applies strict, generalized data-science logic to the prompt.
    Only fires on exact diagnostic scenarios, not general questions.
    """
    query = query.lower()
    rules = []

    # RULE 1: Data Retrieval Requests - only fire on explicit data listing requests
    data_words = ["list", "show me", "tell me", "what fish", "what livestock"]
    if any(phrase in query for phrase in data_words) and any(word in query for word in ["fish", "livestock", "parameter", "log", "reading"]):
        rules.append("""
        EXPERT OVERRIDE: DATA SUMMARY REQUEST
        - The user is explicitly asking to see their data.
        - INSTRUCTION: You MUST write your reply in natural human language.
        """)
        return "\n".join(rules)

    # RULE 2: Universal Biological Cross-Reference - only fire on clear tissue damage
    tissue_keywords = ["chewed", "bitten", "missing flesh", "receding tissue", "coral flesh eaten"]
    if any(phrase in query for phrase in tissue_keywords):
        rules.append("""
        EXPERT OVERRIDE: LIVESTOCK COMPATIBILITY MATRIX
        - INSTRUCTION: Cross-reference affected coral with livestock.
        - FACTS: Dwarf/Flame Angelfish nip LPS corals but ignore SPS.
        - FACTS: Acro-eating flatworms ONLY eat Acropora.
        """)

    # RULE 3: Spatial/Placement Conflict - only fire on explicit placement words
    if any(phrase in query for phrase in ["next to", "right next to", "too close to"]):
        rules.append("""
        EXPERT OVERRIDE: SPATIAL CONFLICT ANALYSIS
        - Check for lighting/flow discrepancies between neighboring corals.
        """)

    # RULE 4: Systemic vs Localized - only fire on all+corals+dying/bleaching
    if query.startswith("all my coral") or ("all corals" in query and any(w in query for w in ["dying", "bleaching", "closed", "not opening"])):
        rules.append("""
        EXPERT OVERRIDE: SYSTEMIC CRASH
        - Tank-wide issue indicates water chemistry problem.
        - INSTRUCTION: Demand testing of Alkalinity, Temp, Salinity if missing.
        """)

    # Default Rule
    if not rules:
        rules.append("EXPERT RULE: Evaluate the vector context and parameter logs normally.")
    
    return "\n".join(rules)

def get_diagnosis_context(query: str, warning_parameters: List[str], current_values: Dict) -> str:
    routing_rules = get_expert_routing_rules(query)
    context = f"""
    ### DATA SCIENCE DIAGNOSTIC RULES ###
    {routing_rules}
    
    ### CURRENT KNOWN PARAMETERS ###
    {current_values if current_values else "No current parameters provided."}
    """
    return context