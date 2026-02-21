#!/usr/bin/env bash
set -euo pipefail

NS="workload-demo"

usage() {
  echo "Usage: $0 {deploy|load|observe|clean}"
}

ensure_ns() {
  kubectl apply -f infra/k8s/00-namespace.yaml
}

install_metrics_server_if_needed() {
  if kubectl get deployment metrics-server -n kube-system >/dev/null 2>&1; then
    echo "[ok] metrics-server already installed"
    return
  fi
  echo "[info] metrics-server not found. Installing..."
  kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
  kubectl rollout status deployment/metrics-server -n kube-system --timeout=180s || true
}

build_images() {
  echo "[info] Building local images..."
  docker build -t workload-demo/api:local services/api
  docker build -t workload-demo/classifier:local services/classifier
  docker build -t workload-demo/worker-light:local services/worker-light
  docker build -t workload-demo/worker-heavy:local services/worker-heavy

  if kubectl config current-context | grep -qi kind; then
    echo "[info] Loading images into kind..."
    kind load docker-image workload-demo/api:local
    kind load docker-image workload-demo/classifier:local
    kind load docker-image workload-demo/worker-light:local
    kind load docker-image workload-demo/worker-heavy:local
  fi
}

deploy_all() {
  ensure_ns
  install_metrics_server_if_needed

  kubectl -n "$NS" apply -f infra/k8s/10-kafka.yaml
  kubectl -n "$NS" rollout status deployment/kafka --timeout=180s

  kubectl -n "$NS" apply -f infra/k8s/11-kafka-topics-init.yaml
  kubectl -n "$NS" wait --for=condition=complete job/kafka-topics-init --timeout=180s || true

  kubectl -n "$NS" apply -f infra/k8s/20-api.yaml
  kubectl -n "$NS" apply -f infra/k8s/21-classifier.yaml
  kubectl -n "$NS" apply -f infra/k8s/22-worker-light.yaml
  kubectl -n "$NS" apply -f infra/k8s/23-worker-heavy.yaml
  kubectl -n "$NS" apply -f infra/k8s/30-hpa.yaml

  kubectl -n "$NS" rollout status deployment/api --timeout=180s
  kubectl -n "$NS" rollout status deployment/classifier --timeout=180s
  kubectl -n "$NS" rollout status deployment/worker-light --timeout=180s
  kubectl -n "$NS" rollout status deployment/worker-heavy --timeout=180s

  echo
  echo "[ok] Deployed."
  echo "Port-forward API:"
  echo "  kubectl -n $NS port-forward svc/api 8080:80"
}

load() {
  echo "[info] Port-forwarding API to localhost:8080 (background)..."
  kubectl -n "$NS" port-forward svc/api 8080:80 >/tmp/workload-demo-portforward.log 2>&1 &
  PF_PID=$!
  trap 'kill $PF_PID >/dev/null 2>&1 || true' EXIT
  sleep 1
  python3 scripts/loadgen.py --base-url http://localhost:8080 --jobs 200 --heavy-ratio 0.35
  echo "[ok] Load sent."
}

observe() {
  echo "[info] Watching HPA + pods (Ctrl+C to stop)"
  echo "In another terminal:"
  echo "  kubectl -n $NS logs -f deploy/classifier"
  echo "  kubectl -n $NS logs -f deploy/worker-heavy"
  echo "  kubectl -n $NS logs -f deploy/worker-light"
  echo
  kubectl -n "$NS" get hpa,pods -w
}

clean() {
  kubectl delete ns "$NS" --ignore-not-found
}

cmd="${1:-}"
case "$cmd" in
  deploy) build_images; deploy_all ;;
  load) load ;;
  observe) observe ;;
  clean) clean ;;
  *) usage; exit 1 ;;
esac
