# Kubernetes Intelligent Workload Orchestrator (Kafka + Autoscaling + Observability Hooks)

A small, production-inspired demo that shows how to run **bursty, compute-intensive jobs** alongside a **high-throughput API** on Kubernetes using:

- **Kafka** for durable, decoupled ingestion
- A **Workload Classifier** that routes jobs to **light** vs **heavy** worker pools
- **Separate Deployments + HPAs** per worker class (so heavy jobs don’t destabilize light workloads)
- **OpenTelemetry hooks** (optional) for traces/metrics (kept minimal)

This is an **AI-adjacent infrastructure demo**: the “intelligence” is the ability to **predict resource class** (light vs heavy) before scheduling. The classifier is intentionally simple (heuristic + optional ML stub), but the infrastructure patterns match real-world platform needs.

---

## What you get

- `services/api` — REST API to submit jobs and query status (pod-local status store for demo)
- `services/classifier` — consumes `jobs.in`, classifies, publishes to `jobs.light` or `jobs.heavy`
- `services/worker-light` — consumes `jobs.light`, simulates fast processing
- `services/worker-heavy` — consumes `jobs.heavy`, simulates CPU/memory-heavy processing
- `infra/k8s` — minimal Kubernetes YAML (Kafka + services + HPAs)
- `scripts/demo.sh` — **3-step demo** (deploy → generate load → observe)

---

## Quickstart (3 steps)

```bash
bash scripts/demo.sh deploy
bash scripts/demo.sh load
bash scripts/demo.sh observe
```

- `deploy` builds local images, deploys Kafka + services + HPAs (and installs metrics-server if missing)
- `load` sends a mixed workload to the API
- `observe` watches HPAs/pods and suggests log commands

---

## Prerequisites

- Kubernetes cluster (kind/minikube OK)
- `kubectl`
- Docker (to build local images)
- Python 3.11+ (for `scripts/loadgen.py`)
- metrics-server (required for HPA; script can install)

---

## Demo endpoints

The script will port-forward the API to `http://localhost:8080` during `load`.

Submit a light job:
```bash
curl -s -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{"fileSizeMb": 12, "pageCount": 40, "imageCount": 2}'
```

Submit a heavy job:
```bash
curl -s -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{"fileSizeMb": 145, "pageCount": 980, "imageCount": 220}'
```

Get status (pod-local demo store):
```bash
curl -s http://localhost:8080/jobs/<jobId>
```

---

## Expected behavior

- The classifier routes heavy jobs only to `worker-heavy`.
- `worker-heavy` has higher memory requests/limits and scales independently.
- `worker-light` remains stable under heavy bursts.
- HPAs scale based on CPU (workers include optional CPU burn to demonstrate scaling).

---

## Repository layout

```
.
├── README.md
├── docs/
│   └── architecture.md
├── infra/
│   └── k8s/
│       ├── 00-namespace.yaml
│       ├── 10-kafka.yaml
│       ├── 11-kafka-topics-init.yaml
│       ├── 20-api.yaml
│       ├── 21-classifier.yaml
│       ├── 22-worker-light.yaml
│       ├── 23-worker-heavy.yaml
│       ├── 30-hpa.yaml
│       └── 40-ingress-optional.yaml
└── scripts/
    ├── demo.sh
    └── loadgen.py
```

---

## Notes on “AI-adjacent”

This demo intentionally focuses on **infrastructure operationalization**:
- intelligent routing
- isolation + scaling governance
- durability via Kafka
- observability hooks

You can later swap the heuristic classifier with a real ML model (ONNX/sklearn) without changing the infrastructure.

---

## License

MIT (see `LICENSE`)
