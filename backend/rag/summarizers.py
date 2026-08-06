import json

async def summarize_telemetry(client, raw_logs: str, user_prompt: str) -> dict:
    """
    Condenses thousands of raw telemetry data points into a short 2-3 sentence summary.
    """
    if not raw_logs or len(raw_logs) < 10:
        return {"type": "telemetry", "content": "No recent telemetry logs available.", "found_issue": False, "tokens": 0}
        
    prompt = f"""
    You are an expert marine biologist analyzing telemetry logs for a reef tank.
    The user is asking: "{user_prompt}"
    
    Review the following raw parameter logs (oldest to newest):
    {raw_logs}
    
    In 2 to 3 sentences, summarize the current stability of the tank. 
    Explicitly call out any significant drops, spikes, or dangerous trends in Alkalinity, Calcium, Magnesium, pH, Temp, or Salinity.
    Contrast the older readings with the most recent ones to catch sudden jumps or crashes.
    CRITICAL INSTRUCTION: DO NOT hallucinate drops or spikes that do not exist in the logs.
    
    If you find ANY parameter that has recently spiked or dropped out of normal reef boundaries (e.g., Alk jumping above 10 or dropping below 7, Calcium above 480 or below 380, Temp fluctuating by more than 2 degrees), this is a MASSIVE anomaly.
    If you find such an anomaly that explains the user's issue, you MUST set `found_issue` to true. If everything is completely stable, set it to false.
    
    Respond STRICTLY in this JSON format:
    {{
        "content": "Your 2-3 sentence summary here",
        "found_issue": true/false
    }}
    """
    
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=300,
        response_format={"type": "json_object"}
    )
    
    try:
        data = json.loads(response.choices[0].message.content)
        return {
            "type": "telemetry",
            "content": data.get("content", "Error parsing response"),
            "found_issue": data.get("found_issue", False),
            "tokens": response.usage.total_tokens
        }
    except Exception:
        return {"type": "telemetry", "content": "Error extracting JSON", "found_issue": False, "tokens": 0}

async def summarize_history(client, tank_profile: str, past_messages: str, tank_events: str, user_prompt: str) -> dict:
    """
    Summarizes the tank profile, notes, and recent conversational history.
    """
    prompt = f"""
    You are an expert marine biologist reviewing a client's tank history.
    The user is asking: "{user_prompt}"
    
    Tank Profile (Livestock):
    {tank_profile}
    
    Tank Notes (Events):
    {tank_events}
    
    Recent Chat History:
    {past_messages}
    
    In 2 to 3 sentences, summarize the tank's contents and any recent issues the user has been discussing or logging in their notes.
    If you find a glaring issue in the tank profile or notes (e.g., a known aggressive fish like a Clown Triggerfish in the same tank, or a specific note about fish fighting) that directly explains the user's problem, set `found_issue` to true. If not, set `found_issue` to false.
    
    Respond STRICTLY in this JSON format:
    {{
        "content": "Your 2-3 sentence summary here",
        "found_issue": true/false
    }}
    """
    
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=300,
        response_format={"type": "json_object"}
    )
    
    try:
        data = json.loads(response.choices[0].message.content)
        return {
            "type": "history",
            "content": data.get("content", "Error parsing response"),
            "found_issue": data.get("found_issue", False),
            "tokens": response.usage.total_tokens
        }
    except Exception:
        return {"type": "history", "content": "Error extracting JSON", "found_issue": False, "tokens": 0}

async def retrieve_knowledge(client, user_prompt: str) -> dict:
    """
    Queries for relevant playbooks or general biological facts based on user symptoms.
    """
    from rag.vector_db import get_vector_context
    vector_context = get_vector_context(user_prompt, k=3)
    
    prompt = f"""
    You are an expert reef knowledge retriever.
    The user is asking: "{user_prompt}"
    
    Vector DB Knowledge:
    {vector_context}
    
    If they are describing a disease, pathology, or coral issue (e.g., bleaching, RTN, melting), output 2-3 sentences of expert factual knowledge summarizing the potential causes and treatments FROM THE VECTOR DB KNOWLEDGE. 
    If the vector DB knowledge is completely irrelevant to their issue, or it's a general question (like adding a fish), output "No specific playbook needed."
    
    If the vector DB explicitly lists the exact symptoms the user is experiencing and provides a clear cause (e.g., Amino Toxicity causing mushrooms to melt), set `found_issue` to true. Otherwise, set it to false.
    
    Respond STRICTLY in this JSON format:
    {{
        "content": "Your 2-3 sentence factual summary here",
        "found_issue": true/false
    }}
    """
    
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=300,
        response_format={"type": "json_object"}
    )
    
    try:
        data = json.loads(response.choices[0].message.content)
        return {
            "type": "knowledge",
            "content": data.get("content", "Error parsing response"),
            "found_issue": data.get("found_issue", False),
            "tokens": response.usage.total_tokens
        }
    except Exception:
        return {"type": "knowledge", "content": "Error extracting JSON", "found_issue": False, "tokens": 0}

async def analyze_equipment_and_notes(client, tank_profile: str, tank_events: str, user_prompt: str) -> dict:
    """
    Analyzes equipment logged by the user and any specific tank notes to see if missing equipment relates to the user's issue.
    """
    prompt = f"""
    You are an Equipment & Tank Notes Analyst.
    
    Tank Profile (Livestock/Equipment):
    {tank_profile}
    
    Tank Notes (Events):
    {tank_events}
    
    User Issue: "{user_prompt}"
    
    Review the user's issue. Identify if they are missing any critical equipment that might relate to their issue (e.g. no skimmer for high nutrients, no heater for temp drops). 
    Check if they have explicitly noted that they DO NOT have that equipment in their Tank Notes.
    Output 1-2 sentences summarizing relevant equipment they have, are missing, or notes indicating they don't have it.
    
    If the missing equipment or a recent tank note directly and obviously explains the user's issue (e.g., Heater failed and temp dropped causing coral shrinkage), set `found_issue` to true. Otherwise, set it to false.
    
    Respond STRICTLY in this JSON format:
    {{
        "content": "Your 1-2 sentence summary here",
        "found_issue": true/false
    }}
    """
    
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=300,
        response_format={"type": "json_object"}
    )
    
    try:
        data = json.loads(response.choices[0].message.content)
        return {
            "type": "equipment_notes",
            "content": data.get("content", "Error parsing response"),
            "found_issue": data.get("found_issue", False),
            "tokens": response.usage.total_tokens
        }
    except Exception:
        return {"type": "equipment_notes", "content": "Error extracting JSON", "found_issue": False, "tokens": 0}
