import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ReefGPT API")

# --- INITIALIZATION ---
# 1. Initialize Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 2. Initialize Groq (using OpenAI client)
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# 3. Allow Frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class ChatRequest(BaseModel):
    text: str

class LogRequest(BaseModel):
    parameter: str
    value: float


TEMP_USER_ID = "00000000-0000-0000-0000-000000000000"

# --- ENDPOINTS ---

@app.get("/get-logs")
def get_logs():
    response = supabase.table("metrics_log").select("*").eq("user_id", "00000000-0000-0000-0000-000000000000").order("timestamp", desc=False).execute()
    return {"data": response.data}

@app.get("/get-chat-history")
def get_chat_history():
    response = supabase.table("chat_history").select("*").eq("user_id", "00000000-0000-0000-0000-000000000000").order("id", desc=False).execute()
    return {"data": response.data}

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        # Update this to pull from metrics_log as well
        history = supabase.table("metrics_log").select("*").order("id", desc=True).limit(10).execute()
        context = f"Recent Tank Logs: {history.data}"
    except Exception:
        context = "No tank logs found yet."

    system_instruction = f"""
You are ReefGPT, a specialized advisor for reef aquariums. 

KNOWLEDGE BOUNDARY:
- You ONLY have expertise in saltwater reef chemistry, coral care, and aquarium hardware.
- You have access to the user's tank data: {context}
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
def log_metric(req: LogRequest):
    try:
        # We change 'tank_settings' to 'metrics_log'
        # And change 'parameter_name' to 'parameter' to match your SQL
        data = {
            "parameter": req.parameter, 
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