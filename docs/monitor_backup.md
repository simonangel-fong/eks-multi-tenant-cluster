# phase 8 — observability

**goal:** in-cluster Grafana dashboard showing RPS / errors / latency for the voting app + postgres, deployed via ArgoCD.

**stack:** `kube-prometheus-stack` (Prometheus + Grafana + Alertmanager + node-exporter + kube-state-metrics), from the `prometheus-community` Helm repo.

---

## steps

| #   | step                 | description                                                                 |
| --- | -------------------- | --------------------------------------------------------------------------- |
| 1   | enable app metrics   | instrument FastAPI to expose `/metrics` (RPS, latency, status codes)        |
| 2   | install prom-grafana | add ArgoCD Application for `kube-prometheus-stack` in `monitoring` ns       |
| 3   | update helm          | add ServiceMonitor to voting-app chart so Prometheus scrapes `/metrics`     |
| 4   | import dashboard     | use community dashboards (FastAPI, postgres, kube) — no custom dashboards   |

---

## exit criteria

- `kubectl port-forward svc/grafana 3000` shows the voting-app dashboard with live traffic
- prometheus targets all `UP`
- ArgoCD reports `Synced` / `Healthy`

---

## Development

```sh
# app monitor package and update codes
cd app
uv lock
uv sync

# confirm
docker compose up --build -d

# 3. generate a bit of traffic
curl http://localhost:8000/
curl http://localhost:8000/polls
curl http://localhost:8000/healthz

# 4. check /metrics exposes prometheus text format
curl http://localhost:8000/metrics | grep "http_requests_total|http_request_duration_seconds_bucket"


helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --version 87.10.1 --create-namespace


 helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --version 87.10.1 --create-namespace -f argocd\apps\values-kps.yaml

kubectl get secret --namespace monitoring -l app.kubernetes.io/component=admin-secret -o jsonpath="{.items[0].data.admin-password}" | base64 --decode ; echo

kubectl -n monitoring port-forward svc/prometheus-grafana 3000:80
```