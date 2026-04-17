"""
ReefGPT API
=========
FastAPI backend for ReefGPT - a reef aquarium management assistant.

Main Features:
- Chat with ReefGPT (with RAG context from vector DB)
- Log water parameters to Supabase
- Predict tank state and forecast chemistry
- Get recommendations based on tank data
"""

import os
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="ReefGPT API")

# ============================================================================
# INITIALIZATION
# ============================================================================

# 1. Connect to Supabase (database for storing logs and chat history)
#    - SUPABASE_URL: Your Supabase project URL
#    - SUPABASE_KEY: Your Supabase API key
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 2. Initialize Groq LLM client (using OpenAI-compatible API)
#    - Uses Llama 3.1 8B for fast, good quality responses
#    - Groq provides free/low-cost inference
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# 3. Enable CORS for frontend connection
#    - Allows localhost:3000 (Next.js dev server) to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
# ============================================================================
# DATA MODELS
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for /chat endpoint."""
    text: str  # User's question

class LogRequest(BaseModel):
    """Request model for /log-metric endpoint."""
    parameter: str  # Parameter name (e.g., "Alkalinity", "Calcium")
    value: float    # Parameter value (e.g., 8.5, 420)


# Default user ID for demo accounts
TEMP_USER_ID = "00000000-0000-0000-0000-000000000000"


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/get-logs")
def get_logs():
    """
    Get water parameter logs from Supabase.
    
    Returns the most recent parameter readings for the demo user.
    """
    response = supabase.table("metrics_log").select("*").eq("user_id", TEMP_USER_ID).order("timestamp", desc=False).execute()
    return {"data": response.data}


@app.get("/data/synthetic")
def get_synthetic_data():
    """
    Generate and return synthetic reef tank data.
    
    Returns generated data with all 5 parameters as time series.
    """
    from data_loader import generate_synthetic_data
    df = generate_synthetic_data(n_days=30)
    
    records = []
    for _, row in df.iterrows():
        for param in ["Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"]:
            if param in row.index and pd.notna(row[param]):
                records.append({
                    "timestamp": row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else str(row["timestamp"]),
                    "parameter": param,
                    "value": float(row[param]),
                    "source": "synthetic",
                })
    
    return {"data": records, "count": len(records)}


@app.get("/data/csv")
def get_csv_data():
    """
    Get data from test_data.csv file.
    
    Returns CSV data as parameter log format.
    """
    try:
        df = pd.read_csv("test_data.csv")
        
        records = []
        for _, row in df.iterrows():
            for param in ["Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"]:
                if param in row.index and pd.notna(row[param]):
                    records.append({
                        "timestamp": str(row["timestamp"]),
                        "parameter": param,
                        "value": float(row[param]),
                        "source": "csv",
                    })
        
        return {"data": records, "count": len(records)}
    except FileNotFoundError:
        return {"data": [], "count": 0, "error": "test_data.csv not found"}


@app.get("/get-chat-history")
def get_chat_history():
    """
    Get chat history from Supabase.
    
    Returns previous messages for conversation context.
    """
    response = supabase.table("chat_history").select("*").eq("user_id", TEMP_USER_ID).order("id", desc=False).execute()
    return {"data": response.data}


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    """
    Main chat endpoint with RAG integration.
    
    This endpoint implements Retrieval-Augmented Generation (RAG):
    1. Get user's question
    2. Search vector DB for relevant knowledge
    3. Get tank data from Supabase
    4. Inject context into LLM prompt
    5. Get LLM response
    6. Save to chat history
    
    Args:
        req.text: User's question about their reef tank
        
    Returns:
        {"reply": "LLM's response text"}
    """
    # Get the user's recent tank readings
    try:
        history = supabase.table("metrics_log").select("*").order("id", desc=True).limit(10).execute()
        tank_data = f"Recent Tank Logs: {history.data}"
    except Exception:
        tank_data = "No tank logs found yet."

    # ============================================================================
    # RAG CONTEXT GATHERING
    # ============================================================================
    # We gather context from 3 sources for better answers:
    
    try:
        from rag import get_diagnosis_context, get_reef_advice
        from scraper import get_recommendation_system
        from vector_db import get_vector_context
        
        # Extract current tank values for diagnosis
        current_vals = {}
        if history.data:
            for row in history.data:
                param = row.get("parameter", "")
                val = row.get("value", 0)
                if param and val:
                    current_vals[param] = val
        
        # 1. Basic diagnosis from rag.py (parameter-based)
        #    E.g., temperature < 76 → "heater_malfunction"
        rag_context = get_diagnosis_context(list(current_vals.keys()), current_vals) if current_vals else ""
        
        # 2. Scraped recommendations from scraper.py (treatments table)
        #    E.g., "Check heater is plugged in..."
        collector = get_recommendation_system()
        scraper_context = collector.get_recommendation_context(
            list(current_vals.keys()), 
            current_vals
        ) if current_vals else ""
        
        # 3. VECTOR DATABASE (most important!)
        #    This searches 1377 reef knowledge vectors for relevant info
        #    based on the USER'S QUESTION, not just parameters.
        #    This is what enables ReefGPT to answer questions about:
        #    - "How do I set up a calcium reactor?"
        #    - "Why is my pH low?"
        #    - "What lighting do I need?"
        vector_context = get_vector_context(req.text, k=3)
        
        # Combine all context sources
        full_context = "\n\n".join([
            vector_context,
            rag_context,
            scraper_context
        ])
        full_context = full_context.strip() or "(Knowledge base unavailable)"
    except Exception as e:
        full_context = f"(RAG unavailable: {e})"

    # ============================================================================
    # BUILD LLM PROMPT
    # ============================================================================
    
    system_instruction = f"""
You are ReefGPT, a specialized advisor for reef aquariums. 

KNOWLEDGE BOUNDARY:
- You ONLY have expertise in saltwater reef chemistry, coral care, and aquarium hardware.
- You have access to the user's tank data: {tank_data}
- {full_context}
- Respond shortly and concisely for most prompts, unless the user specifically asks for or requires a longer explaination.
- If asked about politics, sports, general history, or anything outside of reefing, respond: 
  "I apologize, but my expertise is strictly limited to reef aquarium management. I cannot assist with that topic."

DATA USAGE:
- Refer to the provided tank logs to answer questions about trends.
- If no data is present, suggest the user manually log their Alkalinity using the sidebar.
"""

    # 1. Save User Message
    supabase.table("chat_history").insert({"role": "user", "content": req.text, "user_id": "00000000-0000-0000-0000-000000000000"}).execute()

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant", 
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": req.text}
        ]
    )
    
    reply_text = response.choices[0].message.content
    
    # 2. Save AI Reply
    supabase.table("chat_history").insert({"role": "ai", "content": reply_text, "user_id": "00000000-0000-0000-0000-000000000000"}).execute()

    return {"reply": reply_text}

@app.post("/log-metric")
@app.post("/log-metric")
def log_metric(req: LogRequest):
    """
    Log a water parameter reading.
    
    Validates against physical limits before saving:
    - pH must be between 0 and 14
    - Temperature must be between 32°F and 120°F
    - Calcium must be 0-5000 ppm
    - Magnesium must be 0-5000 ppm
    - Alkalinity must be 0-20 dKH
    
    Returns:
        {"status": "success"} or {"status": "error", "message": "..."}
    """
    from features import validate_parameter, normalize_param_name
    
    # Normalize parameter name (handles "alk" -> "Alkalinity", etc.)
    normalized_param = normalize_param_name(req.parameter)
    if not normalized_param:
        return {"status": "error", "message": f"Unknown parameter: {req.parameter}"}
    
    # Validate against physical limits
    is_valid, error_message = validate_parameter(normalized_param, req.value)
    if not is_valid:
        return {"status": "error", "message": error_message}
    
    try:
        data = {
            "parameter": normalized_param, 
            "value": req.value,
            "user_id": "00000000-0000-0000-0000-000000000000"
        }
        response = supabase.table("metrics_log").insert(data).execute()
        return {"status": "success"}
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        return {"status": "error", "message": str(e)}

@app.delete("/reset-logs")
def reset_logs():
    response = supabase.table("tank_settings").delete().neq("id", 0).execute()
    return {"status": "success", "message": "All logs cleared from memory."}

@app.delete("/delete-logs")
def delete_logs(parameter: str = None):
    """Delete logs - all, by parameter, or by ID."""
    try:
        if parameter:
            response = supabase.table("metrics_log").delete().eq("parameter", parameter).execute()
            return {"status": "success", "deleted": len(response.data) if response.data else 0, "parameter": parameter}
        else:
            response = supabase.table("metrics_log").delete().neq("id", 0).execute()
            return {"status": "success", "deleted": len(response.data) if response.data else 0}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- PREDICTION ENDPOINTS ---

_predictor = None

@app.get("/predict/state")
def predict_state():
    from inference import create_predictor
    global _predictor
    if _predictor is None:
        _predictor = create_predictor()
    return _predictor.predict_current_state()

@app.get("/predict/full-analysis")
def full_analysis(source: str = "auto"):
    """Get full analysis. source=csv|supabase|synthetic|auto"""
    from inference import create_predictor
    global _predictor
    if _predictor is None:
        _predictor = create_predictor()
    
    _predictor.load_data(source)
    
    return _predictor.get_full_analysis()

@app.post("/predict/generate-synthetic")
def generate_synthetic():
    """Generate new synthetic data"""
    from data_loader import generate_synthetic_data
    df = generate_synthetic_data(n_days=30)
    df.to_csv("test_data.csv", index=False)
    return {"status": "success", "rows": len(df)}


# --- MODEL ASSESSMENT ENDPOINT ---

@app.get("/assess-model")
def assess_model_endpoint(
    train_samples: int = 200,
    test_samples: int = 50,
    failure_mode: str = None,
):
    """
    Assess ML model performance.
    
    Generates synthetic train/test data and evaluates models.
    
    Query params:
    - train_samples: Days of training data (default: 200)
    - test_samples: Days of test data (default: 50)
    - failure_mode: Optional 'heater_malfunction', 'dosing_pump_clog', etc.
    
    Returns:
        {
            "classifier": {accuracy, precision, recall, f1_scores, confusion_matrix},
            "regression": {parameter: {rmse, mae, r2_score, ...}}
        }
    """
    os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/opt/libomp/lib:' + os.environ.get('DYLD_LIBRARY_PATH', '')
    
    from assess_model import run_assessment, print_assessment
    
    results = run_assessment(
        n_train=train_samples,
        n_test=test_samples,
        failure_mode=failure_mode if failure_mode != "" else None,
    )
    
    print_assessment(results)
    
    return results