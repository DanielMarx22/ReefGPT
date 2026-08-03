# ReefGPT

ReefGPT is an AI-powered B2B API designed to be seamlessly integrated into existing reef tracking applications (like Neptune Systems and Reeftrak). It functions as a custom, expert-level reef agent that operates on a user's individual tank data combined with an extensively trained knowledge base.

## Product Vision & Roadmap

ReefGPT is transitioning into a robust, multi-tenant API to serve enterprise partners. 

### Planned Features:
- **B2B API & User Login**: Secure API endpoints with authentication to support multiple apps and individual user accounts.
- **Expert-Level Training Data**: Drastically expanding the knowledge cache and scraped data to give the agent the insight of an extremely experienced reefkeeper.
- **Model Accuracy Improvements**: Upgrading the core model to provide hyper-accurate diagnostics and forecasting for individual tanks.

### Deprecations:
- Removed legacy features originally built for school projects (such as the MLP Neural Network), focusing the system entirely on production-grade models (like XGBoost).

## Project Structure

```
ReefGPT/
├── backend/               # FastAPI Python backend
│   ├── api/
│   │   └── main.py        # FastAPI endpoints
│   ├── benchmarks/
│   │   ├── benchmark_rag.py
│   │   └── train.py       # Unified training script
│   ├── ml/
│   │   ├── data_loader.py # Synthetic data generation
│   │   ├── features.py    # Feature engineering
│   │   ├── inference.py   # Rule-based classification
│   │   └── ml_models.py   # Core XGBoost models
│   ├── models/            # Trained models
│   │   └── xgb_model.pkl
│   ├── rag/
│   │   ├── rag.py         # RAG retrieval
│   │   ├── scraper.py     # Knowledge scraper
│   │   └── vector_db.py   # FAISS vector search
│   └── requirements.txt
├── frontend/              # Next.js React frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   └── components/
│   │       ├── Chatbot.tsx
│   │       ├── Dashboard.tsx
│   │       ├── DataView.tsx
│   │       ├── Graphs.tsx
│   │       ├── Navbar.tsx
│   │       └── Readings.tsx
│   └── package.json
├── README.md              # This file
└── .gitignore
```


## Running

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python3 -m uvicorn api.main:app --port 8000
```

**Note**: If you get `ModuleNotFoundError: No module named 'faiss'`, use system Python instead:

```bash
cd backend
pip3 install -r requirements.txt
python3 -m uvicorn api.main:app --port 8000
```

### Frontend (Dashboard UI)

```bash
cd frontend
npm install
npm run dev
```

Access frontend at http://localhost:3000

Backend runs at http://localhost:8000

## Testing the API with curl

```bash
# Get tank status
curl http://localhost:8000/tank-status

# Get recent logs
curl http://localhost:8000/get-logs

# Get profile
curl http://localhost:8000/get-profile

# Log a parameter reading
curl -X POST http://localhost:8000/log-metric \
  -H "Content-Type: application/json" \
  -d '{"parameter_name": "pH", "value": 8.2}'

# Chat with ReefGPT
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Is my tank stable?"}'

# Delete a log entry
curl -X DELETE http://localhost:8000/delete-log/1
```

## Environment Variables

### backend/ and frontend/.env

```
SUPABASE_URL=...
SUPABASE_KEY=...
GROQ_API_KEY=gsk_...
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tank-status` | GET | Current tank state |
| `/get-logs` | GET | Get recent readings |
| `/get-profile` | GET | Get tank profile |
| `/update-profile` | POST | Update tank profile |
| `/log-metric` | POST | Log parameter reading |
| `/chat` | POST | AI chat with ReefGPT |
| `/delete-logs` | DELETE | Delete all logs |
| `/delete-log/{log_id}` | DELETE | Delete a log entry |
| `/get-chat-history` | GET | Get chat history |

## Tank State Classification

### Rule-based (inference.py)

- **Stable**: pH 8.0-8.4, Ca 400-450, Mg 1250-1450, Alk 8.0-9.5
- **Warning**: pH 7.5-8.0, Ca 350-400, Mg 1100-1250, Alk 7.0-8.0
- **Critical**: Outside warning ranges

## Model Training

```bash
cd backend
python3 -m benchmarks.traintest
```

Models saved to `backend/models/`:
- `xgb_model.pkl` - XGBoost classifier

## Dependencies

### Backend
- fastapi, uvicorn
- supabase, python-dotenv
- scikit-learn, xgboost
- pandas, numpy, joblib
- openai
- faiss-cpu, sentence-transformers
- beautifulsoup4, lxml

### Frontend
- react, next
- @supabase/supabase-js
- lucide-react
- chart.js, react-chartjs-2
