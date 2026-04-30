# ReefGPT

Reef aquarium management system with AI diagnostics, ML-based chemistry forecasting, and parameter tracking.

## Project Structure

```
ReefGPT/
├── backend/               # FastAPI Python backend
│   ├── api/
│   │   └── main.py       # FastAPI endpoints
│   ├── benchmarks/
│   │   ├── traintest.py  # Train models (80/20 split)
│   │   ├── benchmark.py # Evaluate models
│   │   ├── backtest.py  # Backtest on historical data
│   │   └── benchmark_rag.py
│   ├── rag/
│   │   ├── rag.py       # RAG retrieval
│   │   ├── vector_db.py # FAISS vector search
│   │   └── scraper.py   # Knowledge scraper
│   ├── tests/
│   │   └── data/       # Test scenarios CSV
│   ├── models/         # Trained models
│   │   ├── xgb_model.pkl
│   │   └── mlp_model.pkl
│   ├── main.py         # Legacy API entry
│   ├── inference.py   # Rule-based classification
│   ├── features.py   # Feature engineering
│   ├── data_loader.py
│   ├── ml_models.py  # XGBoost + MLP classes
│   └── requirements.txt
├── frontend/           # Next.js React frontend
│   ├── src/
│   │   ├── app/      # Pages
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   └── components/
│   │       ├── Dashboard.tsx
│   │       ├── Graphs.tsx
│   │       ├── Readings.tsx
│   │       ├── Chatbot.tsx
│   │       ├── Navbar.tsx
│   │       └── DataView.tsx
│   └── package.json
├── README.md         # This file
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

### Frontend

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

### backend/.env

```
SUPABASE_URL=https://lhvxbuyjjxcyabttwmvu.supabase.co
SUPABASE_KEY=sb_publishable_ESsVlhw0UZzbYUmmlvDO_Q_aPR3ufR7
GROQ_API_KEY=gsk_...
```

### frontend/.env.local

```
NEXT_PUBLIC_SUPABASE_URL=https://lhvxbuyjjxcyabttwmvu.supabase.co
NEXT_PUBLIC_SUPABASE_KEY=sb_publishable_ESsVlhw0UZzbYUmmlvDO_Q_aPR3ufR7
NEXT_PUBLIC_API_PORT=8000
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
- `mlp_model.pkl` - MLP neural network

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
