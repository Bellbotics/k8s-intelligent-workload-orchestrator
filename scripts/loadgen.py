import argparse, random, requests, time

def rand_light():
    return {
        "fileSizeMb": random.randint(1, 20),
        "pageCount": random.randint(1, 120),
        "imageCount": random.randint(0, 15),
    }

def rand_heavy():
    return {
        "fileSizeMb": random.randint(60, 200),
        "pageCount": random.randint(250, 1500),
        "imageCount": random.randint(60, 500),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8080")
    ap.add_argument("--jobs", type=int, default=200)
    ap.add_argument("--heavy-ratio", type=float, default=0.35)
    ap.add_argument("--sleep-ms", type=int, default=10)
    args = ap.parse_args()

    ok = 0
    for _ in range(args.jobs):
        payload = rand_heavy() if random.random() < args.heavy_ratio else rand_light()
        r = requests.post(f"{args.base_url}/jobs", json=payload, timeout=5)
        if r.ok:
            ok += 1
        if args.sleep_ms:
            time.sleep(args.sleep_ms/1000.0)
    print(f"sent={args.jobs} ok={ok}")

if __name__ == "__main__":
    main()
