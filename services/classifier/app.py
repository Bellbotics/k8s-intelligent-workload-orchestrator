import os, json, time
from confluent_kafka import Consumer, Producer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC_IN = os.getenv("TOPIC_IN", "jobs.in")
TOPIC_LIGHT = os.getenv("TOPIC_LIGHT", "jobs.light")
TOPIC_HEAVY = os.getenv("TOPIC_HEAVY", "jobs.heavy")
GROUP = os.getenv("GROUP_ID", "classifier-v1")

def classify(job: dict) -> str:
    if job.get("fileSizeMb", 0) >= 50:
        return "heavy"
    if job.get("pageCount", 0) >= 200:
        return "heavy"
    if job.get("imageCount", 0) >= 50:
        return "heavy"
    return "light"

def main():
    c = Consumer({
        "bootstrap.servers": BOOTSTRAP,
        "group.id": GROUP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })
    p = Producer({"bootstrap.servers": BOOTSTRAP})
    c.subscribe([TOPIC_IN])

    print(json.dumps({"msg": "classifier started", "bootstrap": BOOTSTRAP, "topic": TOPIC_IN}))
    while True:
        msg = c.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(json.dumps({"level":"error","err": str(msg.error())}))
            continue

        job = json.loads(msg.value().decode("utf-8"))
        route = classify(job)
        out_topic = TOPIC_HEAVY if route == "heavy" else TOPIC_LIGHT
        p.produce(out_topic, key=job["jobId"], value=json.dumps(job).encode("utf-8"))
        p.flush(1)

        print(json.dumps({
            "msg": "classified",
            "jobId": job.get("jobId"),
            "route": route,
            "outTopic": out_topic,
            "fileSizeMb": job.get("fileSizeMb"),
            "pageCount": job.get("pageCount"),
            "imageCount": job.get("imageCount"),
            "ts": int(time.time()),
        }))

if __name__ == "__main__":
    main()
