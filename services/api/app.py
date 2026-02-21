from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import os, json, time, uuid
from confluent_kafka import Producer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC_IN = os.getenv("TOPIC_IN", "jobs.in")

producer = Producer({"bootstrap.servers": BOOTSTRAP})

app = FastAPI(title="Workload Demo API", version="1.0")
STATUS = {}  # pod-local demo store

class JobIn(BaseModel):
    fileSizeMb: int = Field(..., ge=1, le=500)
    pageCount: int = Field(..., ge=1, le=5000)
    imageCount: int = Field(..., ge=0, le=5000)

@app.post("/jobs")
def submit_job(job: JobIn):
    job_id = str(uuid.uuid4())
    payload = {
        "jobId": job_id,
        "fileSizeMb": job.fileSizeMb,
        "pageCount": job.pageCount,
        "imageCount": job.imageCount,
        "ts": int(time.time()),
    }
    STATUS[job_id] = {"state": "submitted", "payload": payload}
    producer.produce(TOPIC_IN, key=job_id, value=json.dumps(payload).encode("utf-8"))
    producer.flush(2)
    return {"jobId": job_id, "topic": TOPIC_IN}

@app.get("/jobs/{job_id}")
def get_status(job_id: str):
    if job_id not in STATUS:
        raise HTTPException(status_code=404, detail="jobId not found (demo store is per-pod)")
    return STATUS[job_id]

@app.get("/healthz")
def healthz():
    return {"ok": True}
