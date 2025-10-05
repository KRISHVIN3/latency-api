from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import json

# Load JSON telemetry
with open("telemetry.json") as f:
    data = json.load(f)

# Convert JSON to DataFrame
df = pd.DataFrame(data)

# Rename uptime_pct column to a numeric column if necessary
df["uptime"] = df["uptime_pct"]

# FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Request body model
class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float

@app.post("/latency")
def latency_metrics(req: RequestBody):
    result = {}
    for region in req.regions:
        region_data = df[df["region"] == region]
        if region_data.empty:
            result[region] = None
            continue
        avg_latency = region_data["latency_ms"].mean()
        p95_latency = region_data["latency_ms"].quantile(0.95)
        avg_uptime = region_data["uptime"].mean()
        breaches = (region_data["latency_ms"] > req.threshold_ms).sum()
        result[region] = {
            "avg_latency": float(round(avg_latency, 2)),
            "p95_latency": float(round(p95_latency, 2)),
            "avg_uptime": float(round(avg_uptime, 2)),
            "breaches": int(breaches),
        }
    return result
