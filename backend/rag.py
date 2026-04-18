"""
RAG Diagnostic Router for ReefGPT
Analyzes the prompt to apply Generalized Expert Data Science Rules
before the LLM generates a response.
"""

from typing import List, Dict

def get_expert_routing_rules(query: str) -> str:
    """
    Applies strict, generalized data-science logic to the prompt.
    """
    query = query.lower()
    rules = []

    # RULE 1: Data Retrieval Requests (Keep this one, it formats the UI)
    if any(word in query for word in ["tell", "list", "what", "show"]) and any(word in query for word in ["fish", "livestock", "parameter", "log", "reading"]):
        rules.append("""
        EXPERT OVERRIDE: DATA SUMMARY REQUEST
        - The user is explicitly asking to see their data.
        - INSTRUCTION: You MUST write your `final_user_reply` in natural human language (e.g., "You have 5 yellow tangs... Your recent readings are Alkalinity: 9.0...").
        - INSTRUCTION: Do NOT output JSON arrays or lists of objects inside the `final_user_reply` string. Use conversational text and basic markdown only.
        """)
        return "\n".join(rules) # Exit early so it doesn't try to diagnose a simple list request

    # RULE 2: Universal Biological Cross-Reference
    if any(word in query for word in ["chewed", "bitten", "missing flesh", "receding", "dying", "closed", "bleaching"]):
        rules.append("""
        EXPERT OVERRIDE: LIVESTOCK COMPATIBILITY MATRIX
        - INSTRUCTION: You MUST systematically cross-reference the affected coral with EVERY individual animal in the USER'S LIVESTOCK list.
        - CHEAT SHEET FACTS TO PREVENT HALLUCINATIONS: 
          * Dwarf/Flame Angelfish frequently nip fleshy LPS corals (Acans, Brains) but ignore SPS.
          * Sand-sifting gobies (Diamond Gobies) will bury corals placed on the sandbed.
          * Acro-eating flatworms ONLY eat Acropora (SPS). They NEVER eat Acans (LPS).
          * Tangs generally only eat algae, not coral flesh.
        - INSTRUCTION: If you identify a biological mismatch based on these facts, it MUST be listed as the primary culprit.
        """)

    # RULE 3: Universal Spatial/Placement Conflict
    if any(word in query for word in ["next to", "near", "close", "beside"]):
        rules.append("""
        EXPERT OVERRIDE: SPATIAL CONFLICT ANALYSIS
        - INSTRUCTION: The user mentioned corals in close proximity. You MUST evaluate them for placement mismatches.
        - INSTRUCTION: Check for lighting/flow discrepancies (e.g., SPS needs high flow, LPS needs low flow).
        - INSTRUCTION: Check for physical warfare (e.g., sweeper tentacles from Euphyllia/Torches stinging neighbors).
        """)

    # RULE 4: The Systemic vs Localized Rule (Keep this, it's core Data Science)
    if "all corals" in query and ("dying" in query or "bleaching" in query):
        rules.append("""
        EXPERT OVERRIDE: SYSTEMIC CRASH
        - The user noted a tank-wide issue affecting multiple species.
        - RULE: This indicates a fundamental water chemistry or temperature issue. 
        - INSTRUCTION: If critical parameter logs (Alkalinity, Temp, Salinity) are missing or stale, you MUST demand the user tests them.
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