# Workload contract

What a workload must ship to consume the platform. Kyverno enforces the
must-haves at admission; everything else is the pattern to follow.

## Required (enforced by Kyverno)

Every workload must satisfy these at admission. Failing any of them
blocks the sync.

**On every workload** (`Deployment`, `StatefulSet`, `DaemonSet`, `Job`, `CronJob`, `Rollout`):

- `metadata.labels.team` — routes alerts, dashboards, cost allocation
- Every container has `resources.requests.cpu` and `resources.requests.memory`
- Every container has an explicit image tag (no `:latest`, no untagged)
- Every container has `livenessProbe` and `readinessProbe`
- No privileged containers (`securityContext.privileged: false` or omitted)
- No host namespaces (`hostNetwork`, `hostPID`, `hostIPC`)
- Image pulled from an approved registry: `docker.io`, `quay.io`, `ghcr.io`, `public.ecr.aws`, `registry.k8s.io`, or `*.dkr.ecr.*.amazonaws.com`

**On HTTPRoute**:

- `hostnames` must match the team's assigned subdomain (`<team>.arguswatcher.net` or a sub-subdomain thereof)

**On PrometheusRule** (every alert):

- `annotations.runbook_url` — pointer to how on-call should respond

## Standard patterns (not enforced, but expected)

### Ingress

Attach to the shared Istio Gateway:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: my-app
  namespace: <team>-<env>
spec:
  parentRefs:
    - group: gateway.networking.k8s.io
      kind: Gateway
      name: istio-ingress
      namespace: istio-ingress
      sectionName: https
  hostnames:
    - <team>.arguswatcher.net
  rules:
    - backendRefs:
        - group: ""
          kind: Service
          name: my-app
          port: 8000
          weight: 1
```

DNS and TLS are automatic. No tickets.

### Secrets

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: my-secret
  namespace: <team>-<env>
spec:
  secretStoreRef:
    kind: ClusterSecretStore
    name: aws-secretsmanager
  target:
    name: my-secret
  data:
    - secretKey: <key-in-k8s-secret>
      remoteRef:
        key: <path-in-aws-secretsmanager>
        property: <field-in-json-blob>
```

Coordinate with platform team to grant the ESO IAM role access to your
Secrets Manager path.

### Storage

- `storageClassName: gp3` for general PVCs
- `storageClassName: gp3-iops` for databases and write-heavy stateful workloads
- Both use `WaitForFirstConsumer` — no config needed

### Workload class (if you need database-class nodes)

```yaml
nodeSelector:
  workload-class: database
tolerations:
  - key: workload-class
    value: database
    effect: NoSchedule
```

Without this, workloads land on the `general` class automatically.

### Metrics

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-app
  namespace: <team>-<env>
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: my-app
  endpoints:
    - port: http
      path: /metrics
```

Prometheus auto-discovers. Use route templates in metric labels
(`/polls/:id`, not `/polls/1`) to avoid cardinality explosion.

### Alerts

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: my-app-alerts
  namespace: <team>-<env>
  labels:
    team: <team>
    prometheus: prometheus
    role: alert-rules
spec:
  groups:
    - name: my-app.rules
      rules:
        - alert: MyAppHighErrorRate
          expr: sum(rate(http_requests_total{status=~"5.."}[5m])) > 10
          for: 5m
          labels:
            team: <team>
            severity: warning
          annotations:
            summary: "..."
            description: "..."
            runbook_url: "https://..."   # required by Kyverno
```

Routing to your Slack channel is by `team` label — no Alertmanager
config changes needed.

### Dashboards

Ship as a ConfigMap in your namespace:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-app-dashboard
  namespace: <team>-<env>
  labels:
    grafana_dashboard: "1"
  annotations:
    grafana_folder: "Team: <team>"
data:
  my-app.json: |
    { ... dashboard JSON ... }
```

Grafana sidecar auto-loads. Folder set via `grafana_folder` annotation.

### Progressive delivery

Replace `Deployment` with `Rollout`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
  labels:
    team: <team>
spec:
  strategy:
    canary:
      canaryService: my-app-canary
      stableService: my-app-stable
      trafficRouting:
        plugins:
          argoproj-labs/gatewayAPI:
            httpRoute:
              name: my-app
      steps:
        - setWeight: 10
        - pause: {duration: 2m}
        - analysis:
            templates:
              - templateName: success-rate
                clusterScope: true
            args:
              - {name: service, value: my-app-canary}
              - {name: namespace, value: <team>-<env>}
              - {name: threshold, value: "99"}
        - setWeight: 50
        - pause: {duration: 2m}
        - setWeight: 100
```

Platform provides `ClusterAnalysisTemplate`s: `success-rate`,
`latency-p95`, `error-budget-burn`. Teams reference by name.

## What the platform does NOT ask of teams

Named up front so the boundary is clear:

- **No AWS access.** Teams don't touch AWS console, CLI, or IAM.
- **No kubectl in production.** ArgoCD is the deploy interface; Grafana
  is the observation interface.
- **No mesh primitives.** Teams don't write `VirtualService`,
  `DestinationRule`, `PeerAuthentication`. Gateway API is the boundary.
- **No cluster-scoped resources.** Everything in team namespaces.
  Exceptions handled by platform team on request.
- **No Alertmanager config.** Team-label routing is automatic.
- **No cert-manager `Certificate` resources.** Wildcard cert covers all
  `*.arguswatcher.net` hostnames.
