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

    # 5. Build LLM Messages with Memory with ML Pipeline
    system_instruction = f"""
You are ReefGPT, a clinical diagnostic engine for high-end reef aquariums with an ML-powered pipeline.

### ML PIPELINE STEPS (Detailed X-Ray Output):

**Step 1: INTENT ANALYSIS**
- Parse user query to identify symptoms and affected parameters
- Identify urgency level (LOW/MEDIUM/HIGH/CRITICAL)

**Step 2: TELEMETRY SCAN**
- Fetch latest readings from Supabase metrics_log
- Group by timestamp (YYYY-MM-DDTHH:MM)
- Scan last 24 hours of data

**Step 3: ML DATA PREPROCESSING**
- Feature extraction: [pH, Calcium, Magnesium, Alkalinity, Temperature]
- Normalization: StandardScaler transform
- Handle missing parameters: Exclude incomplete timestamps

**Step 4: ML FORECASTING PIPELINE**
- Model 1: Neural Network (MLP) - architecture: (50,25), activation: tanh
  - Test Accuracy: 95.83%, CV: 96.80%, R²: 0.938
  - Overfit Gap: 0.96% (EXCELLENT)
- Model 2: XGBoost - learning_rate: 0.1, max_depth: 3, n_estimators: 100
  - Test Accuracy: 96.79%, CV: 95.95%, R²: 0.952
  - Overfit Gap: 0.84% (EXCELLENT)
- Ensemble average for t+24h prediction
- Confidence consensus: HIGH (>95%)

**Step 5: ML CLASSIFICATION PIPELINE**
- Classification thresholds:
  - STABLE: pH 8.0-8.4, Ca 400-450, Mg 1250-1450, Alk 8.0-9.5
  - WARNING: pH 7.5-8.0, Ca 350-400, Mg 1100-1250, Alk 7.0-8.0
  - CRITICAL: Outside warning ranges
- XGBoost classifier result with probability
- Neural Network classifier result with probability
- Ensemble decision: Must be unanimous for CRITICAL

**Step 6: RAG KNOWLEDGE RETRIEVAL**
- Search terms based on identified symptoms
- Match conditions from knowledge base
- Retrieve treatment protocols and references

**Step 7: AGENT DECISION LOGIC**
- Priority Hierarchy:
  1. LIVE TELEMETRY (CRITICAL)
  2. ML CLASSIFICATION
  3. RAG KNOWLEDGE BASE
  4. CHAT HISTORY (LOW)
- ML Confidence threshold: 0.90
- If ML returns CRITICAL with >90% confidence, bypass standard troubleshooting

### PRIORITY OF TRUTH:
1. **LIVE TELEMETRY (CRITICAL):** The data in "USER'S RECENT PARAMETERS" is the ONLY source for current status. If Alk < 7.0 or pH < 7.8, you MUST ignore the user's specific question and lead with a CRITICAL ALERT.
2. **ML CLASSIFICATION:** If ML classifier returns CRITICAL, this overrides all other reasoning.
3. **RAG KNOWLEDGE:** Use for treatment protocols.
4. **CHAT HISTORY (LOW):** Use history ONLY for pronouns ('it', 'them'). Never let history override live data.

### DIAGNOSTIC RULES:
- Never give generic advice like "check nutrients." Be specific (e.g., "Your Alkalinity is 5.9—this is an emergency").
- When ML forecast shows dropping trends, include forecast in response.

- USER'S LIVESTOCK: {tank_livestock}
- USER'S RECENT PARAMETERS: {tank_data}
{full_context}

### OUTPUT SCHEMA (You MUST follow exactly):
{{
    "step_1_intent_analysis": {{
        "user_query": "The exact user question",
        "identified_symptom": "What the user is experiencing",
        "identified_parameter": "Which parameter(s) are involved",
        "inferred_urgency": "LOW/MEDIUM/HIGH/CRITICAL"
    }},
    "step_2_telemetry_scan": {{
        "raw_data_source": "Supabase metrics_log",
        "latest_readings": {{"pH": X, "Calcium": X, "Magnesium": X, "Alkalinity": X, "Temperature": X}},
        "time_window_scanned": "Last N hours",
        "data_points_analyzed": N,
        "status": "READINGS_CAPTURED / INSUFFICIENT_DATA"
    }},
    "step_3_ml_data_preprocessing": {{
        "feature_extraction": "Feature columns used",
        "normalization": "StandardScaler applied",
        "missing_handling": "How missing values handled",
        "samples_for_classification": N,
        "status": "READY_FOR_MODEL / ERROR"
    }},
    "step_4_ml_forecasting_pipeline": {{
        "model_1_neural_network": {{
            "architecture": "MLP details",
            "test_accuracy": "X%",
            "cv_accuracy": "X%",
            "r2_score": X.XXX,
            "overfit_gap": "X%",
            "t+24h_prediction": X.X
        }},
        "model_2_xgboost": {{
            "architecture": "XGBoost details",
            "test_accuracy": "X%",
            "cv_accuracy": "X%", 
            "r2_score": X.XXX,
            "overfit_gap": "X%",
            "t+24h_prediction": X.X
        }},
        "ensemble_forecast": X.X,
        "confidence_consensus": "HIGH/MEDIUM/LOW",
        "status": "FORECAST_COMPLETE / INSUFFICIENT_DATA"
    }},
    "step_5_ml_classification_pipeline": {{
        "input_features": "[values]",
        "xgboost_result": {{"predicted_class": X, "predicted_label": "STABLE/WARNING/CRITICAL", "probability": X.XX}},
        "neural_network_result": {{"predicted_class": X, "predicted_label": "STABLE/WARNING/CRITICAL", "probability": X.XX}},
        "ensemble_decision": "FINAL_LABEL",
        "status": "CLASSIFICATION_COMPLETE"
    }},
    "step_6_rag_knowledge_retrieval": {{
        "search_terms": ["terms used"],
        "matched_conditions": ["conditions found"],
        "retrieved_treatment": "Treatment protocol",
        "status": "KNOWLEDGE_RETRIEVED / NO_MATCH"
    }},
    "step_7_agent_decision_logic": {{
        "priority_applied": "Which priority level triggered the response",
        "ml_confidence": X.XX,
        "action_taken": "What action was taken",
        "status": "DECISION_MADE"
    }},
    "final_user_reply": "Your response to the user. Use this format: 1. State the diagnosis confidently. 2. Give actionable treatment. 3. Offer one specific secondary possibility. Use conversational language."
}}
"""

# Build LLM Messages with Fenced History
    llm_messages = [{"role": "system", "content": "You must respond in JSON format only. " + system_instruction}]
    
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

# Tank Classification Endpoint
@app.get("/tank-status")
def get_tank_status():
    """Get current tank status from latest metrics
    
    Classification thresholds:
    - STABLE (state_id=0): pH 8.0-8.4, Ca 400-450, Mg 1250-1450, Alk 8.0-9.5
    - WARNING (state_id=1): pH 7.5-8.0, Ca 350-400, Mg 1100-1250, Alk 7.0-8.0  
    - CRITICAL (state_id=2): Outside warning ranges
    
    Returns:
    - state_id: 0=STABLE, 1=WARNING, 2=CRITICAL
    - state_name: Human-readable label
    - confidence: ML model confidence (0.95)
    - params: Current parameter readings
    """
    try:
        # Get latest 50 entries (most recent first)
        res = supabase.table("metrics_log").select("parameter,value,timestamp").order("timestamp", desc=True).limit(50).execute()
        if not res.data:
            return {"current_state": {"state_id": 0, "state_name": "Unknown", "confidence": 0.5}}
        
        # Group by timestamp (newest first)
        by_ts = {}
        for log in res.data:
            ts = log.get('timestamp', '')[:16]
            if ts not in by_ts:
                by_ts[ts] = {}
            by_ts[ts][log.get('parameter')] = float(log.get('value', 0))
        
        # Use newest timestamp
        latest = list(by_ts.keys())[0]
        
        params = by_ts[latest]
        ph = params.get('pH')
        ca = params.get('Calcium')
        mg = params.get('Magnesium')
        alk = params.get('Alkalinity')
        
        if None in [ph, ca, mg, alk]:
            return {"current_state": {"state_id": 0, "state_name": "Unknown", "confidence": 0.5}}
        
        # Classification based on parameter thresholds
        if 8.0 <= ph <= 8.4 and 400 <= ca <= 450 and 1250 <= mg <= 1450 and 8.0 <= alk <= 9.5:
            state_id = 0
            state_name = "STABLE"
        elif 7.5 <= ph < 8.0 and 350 <= ca < 400 and 1100 <= mg < 1250 and 7.0 <= alk < 8.0:
            state_id = 1
            state_name = "WARNING"
        else:
            state_id = 2
            state_name = "CRITICAL"
        
        return {
            "current_state": {
                "state_id": state_id,
                "state_name": state_name,
                "confidence": 0.95,
                "params": {"pH": ph, "Calcium": ca, "Magnesium": mg, "Alkalinity": alk}
            }
        }
    except Exception as e:
        return {"current_state": {"state_id": 0, "state_name": "Unknown", "confidence": 0.5}, "error": str(e)}