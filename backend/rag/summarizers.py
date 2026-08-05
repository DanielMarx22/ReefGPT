import json

async def summarize_telemetry(client, raw_logs: str) -> dict:
    """
    Condenses thousands of raw telemetry data points into a short 2-3 sentence summary.
    """
    if not raw_logs or len(raw_logs) < 10:
        return {"type": "telemetry", "content": "No recent telemetry logs available.", "tokens": 0}
        
    prompt = f"""
    You are an expert marine biologist analyzing telemetry logs for a reef tank.
    Review the following raw parameter logs (oldest to newest):
    {raw_logs}
    
    In 2 to 3 sentences, summarize the current stability of the tank. 
    Explicitly call out any significant drops, spikes, or dangerous trends in Alkalinity, Calcium, Magnesium, pH, Temp, or Salinity.
    If everything is stable, state that clearly.
    """
    
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    return {
        "type": "telemetry",
        "content": response.choices[0].message.content,
        "tokens": response.usage.total_tokens
    }

async def summarize_history(client, tank_profile: str, past_messages: str) -> dict:
    """
    Summarizes the tank profile and recent conversational history.
    """
    prompt = f"""
    You are an expert marine biologist reviewing a client's tank history.
    
    Tank Profile (Livestock/Equipment):
    {tank_profile}
    
    Recent Chat History:
    {past_messages}
    
    In 2 to 3 sentences, summarize the tank's contents and any recent issues the user has been discussing.
    """
    
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    return {
        "type": "history",
        "content": response.choices[0].message.content,
        "tokens": response.usage.total_tokens
    }

async def retrieve_knowledge(client, user_prompt: str) -> dict:
    """
    Queries for relevant playbooks or general biological facts based on user symptoms.
    """
    prompt = f"""
    You are an expert reef knowledge retriever.
    The user is asking: "{user_prompt}"
    
    If they are describing a disease or coral issue (e.g., bleaching, RTN, white spots), output 2-3 sentences of expert factual knowledge about potential causes. 
    For example, if they mention mushrooms bleaching, mention amino acid toxicity or light shock.
    If it's just a general question or adding a fish, output "No specific playbook needed."
    """
    
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    return {
        "type": "knowledge",
        "content": response.choices[0].message.content,
        "tokens": response.usage.total_tokens
    }

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
    """
    
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    return {
        "type": "equipment_notes",
        "content": response.choices[0].message.content,
        "tokens": response.usage.total_tokens
    }
