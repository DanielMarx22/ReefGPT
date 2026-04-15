# ReefOS Model

Machine learning model for reef aquarium water chemistry forecasting and tank state classification.

## Overview

Analyzes reef tank water parameters and predicts:
- **Tank State**: Stable, Warning, or Critical
- **24-Hour Forecast**: Predicted values for each parameter
- **Recommendations**: Actionable advice based on trends

## Parameters Tracked

| Parameter | Ideal Range | Critical Range |
|-----------|------------|---------------|
| Alkalinity | 7.5-9.5 dKH | 6.5-11.0 dKH |
| Calcium | 400-450 ppm | 350-500 ppm |
| Magnesium | 1250-1450 ppm | 1100-1600 ppm |
| pH | 8.0-8.4 | 7.6-8.6 |
| Temperature | 76-80°F | 72-84°F |

## Mathematical Model

### Velocity Calculation
Rate of change for each parameter:
```
velocity = dX/dt = (X[t] - X[t-1]) / Δt
```

### 24-Hour Prediction
```
predicted_24h = current + (velocity × 4)
```
(Assuming 6-hour sampling intervals)

### Trend Classification
- **stable**: deviation ≤ 50% of ideal range width
- **warning**: deviation 50-100% of ideal range width
- **critical**: deviation > 100% of ideal range width

### Tank State Classification
- **Stable (0)**: All parameters in ideal range
- **Warning (1)**: Any parameter outside ideal but in critical range
- **Critical (2)**: Any parameter outside critical range

## File Structure

```
backend/
├── data_loader.py     # Synthetic data generation
├── features.py        # Velocity, ratios, labels
├── inference.py       # Main prediction engine
├── main.py           # FastAPI server
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

## Installation

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Running

### API Server (Recommended)

```bash
python -m uvicorn main:app --reload
```

Server runs at `http://localhost:8000`

### Endpoints

| Endpoint | Description |
|---------|------------|
| `GET /predict/state` | Current tank state |
| `GET /predict/full-analysis` | Full analysis with forecasts |

### Test

```bash
curl http://localhost:8000/predict/full-analysis
```

### Direct Python

```bash
python3 -c "from inference import create_predictor; print(create_predictor().get_full_analysis())"
```

## API Response Format

```json
{
  "timestamp": "2026-04-14T17:10:34.281399",
  "current_state": {
    "state_id": 0,
    "state_name": "Stable",
    "confidence": 0.9,
    "warning_parameters": []
  },
  "current_values": {
    "Alkalinity": 8.7,
    "Calcium": 404.53,
    "Magnesium": 1317.31,
    "pH": 8.3,
    "Temperature": 79.01
  },
  "forecast_24h": {
    "Alkalinity": {
      "current": 8.7,
      "predicted_24h": 8.69,
      "velocity": -0.0042,
      "trend": "stable"
    },
    ...
  },
  "recommendations": ["Monitor temperature closely"],
  "model_version": "1.0.0"
}
```

## Deployment

### Render / Railway / Fly.io

1. Create `runtime.txt`:
```
python-3.12
```

2. Set environment variables in dashboard:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GROQ_API_KEY=your_groq_api_key
```

3. Start command:
```
pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t reefos .
docker run -p 8000:8000 -e SUPABASE_URL=... reefos
```

## Development

### Running Tests

```bash
cd backend
python3 -c "
from data_loader import generate_synthetic_data
from features import FeatureEngineer, create_labels

df = generate_synthetic_data(n_days=7)
fe = FeatureEngineer()
df_f = fe.create_all_features(df)
df_l = create_labels(df_f)

print(f'Samples: {len(df)}')
print(f'Features: {len(df_f.columns)}')
print(f'States: {dict(df_l.tank_state.value_counts())}')
"
```

### Training Data

The model trains on synthetic data with these failure modes:
- `heater_malfunction` - Temperature drops
- `dosing_pump_clog` - Alkalinity drops  
- `calcifier_depletion` - Calcium & pH drop
- `magnesium_spike` - Magnesium spikes

## License

MIT