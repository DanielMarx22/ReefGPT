import json

async def route_intent(client, user_prompt: str, past_messages: str = "") -> dict:
    """
    Acts as the Orchestrator to determine which subagents should run.
    """
    prompt = f"""
    You are the RAG Orchestrator for ReefGPT.
    
    The user asked: "{user_prompt}"
    
    Recent Chat Context:
    {past_messages}
    
    You have 4 specialized subagents:
    1. "telemetry" - Analyzes raw water parameters (pH, Alk, Calc, Temp).
    2. "historian" - Analyzes the tank's livestock and recent conversational context.
    3. "equipment" - Analyzes the user's hardware (skimmers, heaters) and tank notes/events.
    4. "knowledge" - Searches the Vector DB for general biological/pathological facts.
    
    Your job is to return an ORDERED list of which subagents we should query.
    Rank them from MOST likely to contain the root cause to LEAST likely.
    If the question is purely generic, you can omit 'telemetry' or 'equipment'. 
    If the question is heavily specific to the user's tank, 'telemetry' and 'historian' should be first.
    
    Respond STRICTLY in this JSON format:
    {{
        "subagents": ["telemetry", "knowledge", "equipment", "historian"], // ORDERED by relevance
        "reply": "If SHORT_CIRCUIT, explain why here",
        "status": "PROCEED or SHORT_CIRCUIT"
    }}
    """
    
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=200,
        response_format={"type": "json_object"}
    )
    
    try:
        data = json.loads(response.choices[0].message.content)
        # Ensure it always returns a list
        if not isinstance(data.get("subagents"), list):
            data["subagents"] = ["telemetry", "historian", "equipment", "knowledge"]
        return {"content": data, "tokens": response.usage.total_tokens}
    except Exception:
        return {"content": {"subagents": ["telemetry", "historian", "equipment", "knowledge"], "status": "PROCEED"}, "tokens": 0}
