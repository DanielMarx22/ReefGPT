import json

async def route_intent(client, user_prompt: str, past_messages: str = "") -> dict:
    """
    Acts as the Orchestrator to determine which subagents should run.
    """
    prompt = f"""
    You are the Orchestrator for ReefGPT. Your job is to analyze the user's prompt and determine WHICH subagents are needed to gather enough context for the Master AI.
    
    Available Subagents:
    - "telemetry": Analyzes the tank's numerical parameters (pH, NO3, PO4, Temp, etc.).
    - "historian": Analyzes past chat history and tank event notes to find correlations over time.
    - "equipment": Analyzes the user's tank profile (livestock and equipment) to see if they are missing critical hardware related to their issue.
    - "knowledge": Queries the database for biological or chemical playbooks (e.g., diseases, algae outbreaks, coral health).
    
    User Prompt: "{user_prompt}"
    
    RULES:
    1. Only select the subagents that are relevant to the user's prompt. 
    2. If it's a general question or adding a fish, you might not need "telemetry".
    3. If they mention an issue (e.g., algae, disease, parameters), you usually need all of them.
    4. If the user's prompt is missing critical information required to perform an action (e.g. logging alk without a value, or adding a fish without species/size), set status to SHORT_CIRCUIT and provide the reply.
    
    Respond STRICTLY in JSON format:
    {{
        "status": "SHORT_CIRCUIT" or "PROCEED",
        "reply": "If SHORT_CIRCUIT, put the conversational question here. Else empty.",
        "subagents": ["telemetry", "historian", "equipment", "knowledge"] (array of strings, only include needed ones)
    }}
    """
    
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    
    try:
        data = json.loads(response.choices[0].message.content)
    except Exception:
        data = {"status": "PROCEED", "reply": "", "subagents": ["telemetry", "historian", "equipment", "knowledge"]}
        
    return {
        "type": "orchestrator",
        "content": data,
        "tokens": response.usage.total_tokens
    }
