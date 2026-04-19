"""
ReefGPT API
=========
FastAPI backend for ReefGPT - a reef aquarium management assistant.
"""

import os
import json
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ReefGPT API - Testing Mode")

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    text: str

class LogRequest(BaseModel):
    parameter: str
    value: float

class ProfileRequest(BaseModel):
    livestock: str

TEMP_USER_ID = "00000000-0000-0000-0000-000000000000"

@app.get("/get-profile")
def get_profile():
    res = supabase.table("tank_settings").select("*").eq("user_id", TEMP_USER_ID).execute()
    if res.data:
        return {"livestock": res.data[0].get("livestock", "")}
    return {"livestock": ""}

@app.post("/update-profile")
def update_profile(req: ProfileRequest):
    res = supabase.table("tank_settings").select("*").eq("user_id", TEMP_USER_ID).execute()
    if res.data:
        supabase.table("tank_settings").update({"livestock": req.livestock}).eq("user_id", TEMP_USER_ID).execute()
    else:
        supabase.table("tank_settings").insert({"user_id": TEMP_USER_ID, "livestock": req.livestock}).execute()
    return {"status": "success"}

@app.get("/get-logs")
async def get_logs():
    try:
        response = supabase.table("metrics_log") \
            .select("*") \
            .order("timestamp", desc=True) \
            .limit(3000) \
            .execute()
            
        return {"data": response.data}
    except Exception as e:
        return {"error": str(e)}

@app.get("/get-chat-history")
def get_chat_history():
    response = supabase.table("chat_history").select("*").eq("user_id", TEMP_USER_ID).order("id", desc=False).execute()
    return {"data": response.data}

@app.post("/log-metric")
def log_metric(req: LogRequest):
    try:
        data = {
            "parameter": req.parameter.strip(), 
            "value": req.value,
            "user_id": TEMP_USER_ID
        }
        supabase.table("metrics_log").insert(data).execute()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.delete("/delete-logs")
def delete_logs(parameter: str = None):
    try:
        if parameter:
            response = supabase.table("metrics_log").delete().eq("parameter", parameter).execute()
            return {"status": "success"}
        else:
            response = supabase.table("metrics_log").delete().neq("id", 0).execute()
            return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.delete("/delete-log/{log_id}")
def delete_log(log_id: int):
    try:
        supabase.table("metrics_log").delete().eq("id", log_id).execute()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        # INCREASE LIMIT TO 150 so it actually sees the Alkalinity tests
        history = supabase.table("metrics_log").select("*").order("timestamp", desc=True).limit(150).execute()
        if history.data:
            chrono_logs = sorted(history.data, key=lambda x: x['timestamp'])
            log_strings = [f"[{log['timestamp'][:16]}] {log['parameter']}: {log['value']}" for log in chrono_logs]
            tank_data = "Recent Tank Logs (Chronological, oldest to newest):\n" + "\n".join(log_strings)
        else:
            tank_data = "No tank logs found yet."
    except Exception as e:
        tank_data = "No tank logs found yet."

    # 2. Get Livestock Profile
    try:
        profile = supabase.table("tank_settings").select("livestock").eq("user_id", TEMP_USER_ID).execute()
        tank_livestock = profile.data[0]["livestock"] if profile.data else "No livestock profile found."
    except Exception:
        tank_livestock = "No livestock profile found."

    # 3. Fetch Chat History (Moved UP so RAG can use it)
    try:
        raw_history = supabase.table("chat_history").select("role,content").eq("user_id", TEMP_USER_ID).order("id", desc=True).limit(6).execute()
        past_messages = raw_history.data[::-1] if raw_history.data else []
    except Exception:
        past_messages = []

    # 4. RAG Context (Smart Context-Aware Search)
    try:
        from rag import get_diagnosis_context
        from vector_db import get_vector_context
        
        current_vals = {}
        if history.data:
            for row in history.data:
                param = row.get("parameter", "")
                val = row.get("value", 0)
                if param and val:
                    current_vals[param] = val
        
        # --- THE FIX: Only append history if it's a follow-up ---
        search_query = req.text
        follow_up_triggers = ["it", "they", "them", "this", "that", "he", "she"]
        words = req.text.lower().split()
        is_follow_up = len(words) < 8 or any(word in words for word in follow_up_triggers)

        if is_follow_up and past_messages:
            for msg in reversed(past_messages):
                if msg["role"] == "user":
                    search_query = f"Previous context: {msg['content']} | Current question: {req.text}"
                    break
                
        rag_context = get_diagnosis_context(search_query, list(current_vals.keys()), current_vals)
        vector_context = get_vector_context(search_query, k=3)
        
        full_context = f"--- VECTOR DATABASE RESULTS ---\n{vector_context}\n\n--- EXPERT OVERRIDE RULES (HIGHEST PRIORITY) ---\n{rag_context}"
    except Exception as e:
        full_context = f"(RAG unavailable: {e})"

    # 5. Build LLM Messages with Memory
    system_instruction = f"""
You are ReefGPT, a clinical diagnostic engine for high-end reef aquariums. 

### PRIORITY OF TRUTH:
1. **LIVE TELEMETRY (CRITICAL):** The data in "USER'S RECENT PARAMETERS" is the ONLY source for current status. If Alk < 7.0 or pH < 7.8, you MUST ignore the user's specific question and lead with a CRITICAL ALERT.
2. **KNOWLEDGE BOUNDARY:** You are an expert in Bryopsis, DINs, and chemical crashes.
3. **CHAT HISTORY (LOW PRIORITY):** Use history ONLY for pronouns ('it', 'them'). Never let history override live data.

### DIAGNOSTIC RULES:
- Never give generic advice like "check nutrients." Be specific (e.g., "Your Alkalinity is 5.9—this is an emergency").

- USER'S LIVESTOCK: {tank_livestock}
- USER'S RECENT PARAMETERS: {tank_data}
{full_context}

CRITICAL INSTRUCTION:
You MUST respond ONLY with a valid JSON object. Do not include markdown formatting or any conversational text outside the JSON.
Your JSON must exactly match this schema:
{{
    "trigger": "The user's core problem or question",
    "data_evaluated": ["list", "of", "facts", "considered"],
    "ignored_data": ["list", "of", "missing or irrelevant", "data ignored"],
    "hypothesis": "Your diagnostic reasoning",
    "confidence_score": 0.95,
    "final_user_reply": "The exact message to show the user. When diagnosing, use this format: 1. State the primary culprit confidently. 2. Give actionable advice to fix it. 3. Offer one highly specific secondary possibility based on their livestock or parameters (e.g., 'If it is not the angelfish, check if your goby is burying it'). Use conversational, natural language. DO NOT give generic advice."
}}
"""

# Build LLM Messages with Fenced History
    llm_messages = [{"role": "system", "content": system_instruction}]
    
    if past_messages:
        llm_messages.append({"role": "system", "content": "[START STALE CHAT HISTORY]"})
        for msg in past_messages:
            role = "assistant" if msg["role"] == "ai" else "user"
            llm_messages.append({"role": role, "content": str(msg.get("content", ""))})
        llm_messages.append({"role": "system", "content": "[END STALE CHAT HISTORY - FOCUS ON NEWEST DATA BELOW]"})
        
    llm_messages.append({"role": "user", "content": req.text})        

    # Save User Message to DB
    supabase.table("chat_history").insert({"role": "user", "content": req.text, "user_id": TEMP_USER_ID}).execute()

    # 6. Call LLM
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=llm_messages,
        response_format={"type": "json_object"}
    )
    
    raw_reply = response.choices[0].message.content
    
    try:
        json_data = json.loads(raw_reply)
        user_reply = json_data.get("final_user_reply", "I encountered an error processing that.")
        if not isinstance(user_reply, str):
            user_reply = json.dumps(user_reply, indent=2)
    except json.JSONDecodeError:
        json_data = {"error": "Failed to parse JSON", "raw": raw_reply}
        user_reply = raw_reply

    # Save AI Message to DB
    supabase.table("chat_history").insert({
        "role": "ai", 
        "content": user_reply, 
        "user_id": TEMP_USER_ID,
        "agent_reasoning": json_data
    }).execute()

    return {
        "reply": user_reply,
        "debug_xray": json_data
    }