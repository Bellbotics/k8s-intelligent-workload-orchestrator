# Architecture

This demo implements a common production pattern: **separate a high-QPS API from bursty, compute-heavy async workloads**, and isolate heavy workloads into their own worker pool.

---

## Logical flow

```mermaid
flowchart LR
  client[Client / Loadgen] --> api[API Service]
  api -->|produce| jin[(Kafka topic: jobs.in)]

  jin -->|consume| cls[Workload Classifier]
  cls -->|produce light| jlight[(Kafka topic: jobs.light)]
  cls -->|produce heavy| jheavy[(Kafka topic: jobs.heavy)]

  jlight -->|consume| wL[Worker Pool: Light]
  jheavy -->|consume| wH[Worker Pool: Heavy]

  wL --> out[(Result sink / logs)]
  wH --> out
```

---

## Kubernetes deployment view

```mermaid
flowchart TB
  subgraph NS["Namespace: workload-demo"]
    subgraph K["Kafka - single node (KRaft)"]
      broker[(kafka)]
    end

    api["Deployment: api"] --> svcapi["Service: api"]
    cls["Deployment: classifier"]
    wl["Deployment: worker-light"]
    wh["Deployment: worker-heavy"]

    hpaL["HPA: worker-light"] --> wl
    hpaH["HPA: worker-heavy"] --> wh

    api --> broker
    cls --> broker
    wl --> broker
    wh --> broker
  end
```

---

## Classification logic

Default heuristic:
- If `fileSizeMb >= 50` OR `pageCount >= 200` OR `imageCount >= 50` → **heavy**
- else → **light**

Swap with a real model later if desired.

---

## Scaling strategy

- `worker-light`: smaller CPU/memory requests; HPA targets CPU utilization
- `worker-heavy`: higher memory requests/limits; HPA targets CPU utilization

Core idea: **independent scaling and isolation** so heavy jobs scale heavy workers without destabilizing light processing.
