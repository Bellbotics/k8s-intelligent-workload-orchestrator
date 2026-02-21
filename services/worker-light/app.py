import os, json, time, random
from confluent_kafka import Consumer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC = os.getenv("TOPIC", "jobs.light")
GROUP = os.getenv("GROUP_ID", "worker-light-v1")
WORK_MS_MIN = int(os.getenv("WORK_MS_MIN", "50"))
WORK_MS_MAX = int(os.getenv("WORK_MS_MAX", "300"))
BUSY_CPU = os.getenv("BUSY_CPU", "false").lower() == "true"

def busy_work(ms: int):
    end = time.time() + (ms / 1000.0)
    x = 0
    while time.time() < end:
        x = (x * 3 + 7) % 1000003
    return x

def main():
    c = Consumer({
        "bootstrap.servers": BOOTSTRAP,
        "group.id": GROUP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })
    c.subscribe([TOPIC])
    print(json.dumps({"msg": "worker started", "group": GROUP, "topic": TOPIC, "bootstrap": BOOTSTRAP}))
    while True:
        msg = c.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(json.dumps({"level":"error","err": str(msg.error())}))
            continue

        job = json.loads(msg.value().decode("utf-8"))
        work_ms = random.randint(WORK_MS_MIN, WORK_MS_MAX)
        if BUSY_CPU:
            busy_work(work_ms)
        else:
            time.sleep(work_ms/1000.0)

        print(json.dumps({
            "msg": "processed",
            "jobId": job.get("jobId"),
            "topic": TOPIC,
            "workMs": work_ms,
            "fileSizeMb": job.get("fileSizeMb"),
            "pageCount": job.get("pageCount"),
            "imageCount": job.get("imageCount"),
            "ts": int(time.time()),
        }))

if __name__ == "__main__":
    main()
