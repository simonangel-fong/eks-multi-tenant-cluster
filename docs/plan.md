project: voting system — plan

---

## scope

- single voting service (polls, votes, results in one app)
- postgres in-cluster (no RDS), persisted via EBS CSI
- no auth for now — trust `X-User-Id` header (swap to Cognito later)
- deployed to EKS via ArgoCD (GitOps)

---

## stack

- backend: python — FastAPI, SQLAlchemy, psycopg, pydantic-settings
- migrations: **Flyway** (Java-based; same image for compose + Helm initContainer)
- deps: **uv** (`pyproject.toml` + `uv.lock`)
- db: postgres 16
- container: docker (multi-stage, non-root)
- k8s: EKS, Helm chart, ArgoCD, **Gateway API** (not Ingress)
- iac: terraform (VPC, EKS, IRSA, addons)
- registry: **Docker Hub** today (`simonangelfong/voting-api`) → ECR before EKS
- ci: github actions → registry

---

## repo layout

```
project-eks-argocd/
├─ .github/               # CI workflows (build/push image, terraform plan) — pending
├─ app/                   # python backend
│  ├─ voting/             # FastAPI source (config, db, models, schemas, routers)
│  ├─ tests/              # pytest (real postgres via docker compose)
│  ├─ flyway/sql/         # V*.sql migrations (single source of truth)
│  ├─ Dockerfile          # multi-stage, non-root
│  ├─ pyproject.toml
│  └─ uv.lock
├─ helm/
│  └─ voting-app/         # chart (Deployment, StatefulSet, Gateway, HTTPRoute, tests)
│     ├─ flyway-sql/      # copied from app/flyway/sql — packaged into ConfigMap
│     ├─ templates/
│     ├─ values.yaml
│     ├─ values-dev.yaml
│     └─ values-prod.yaml
├─ argocd/                # Application manifests (GitOps entry points) — pending
├─ terraform/             # EKS, VPC, IRSA, addons, gp3 StorageClass — pending
├─ docs/                  # design + plan + per-phase notes (01-data, 02-app, 03-helm, ...)
├─ sql/                   # seed + tally + duplicate-vote checks for local dev
│  └─ initdb/             # bootstrap: creates voting_test db for pytest
└─ docker-compose.yml     # local dev stack (postgres + flyway + flyway-test + api)
```

---

## api

```
POST   /polls                → create poll
GET    /polls                → list polls
GET    /polls/{id}           → poll details
POST   /polls/{id}/vote      → cast vote (reads X-User-Id)
GET    /polls/{id}/results   → tally
GET    /healthz /readyz      → probes
```

See [02-app.md](02-app.md) for the full request/response/error table.

---

## schema

```sql
polls    (id, title, created_at, closes_at)
options  (id, poll_id, label)
votes    (id, poll_id, option_id, voter_id, created_at,
          UNIQUE(poll_id, voter_id))
```

`UNIQUE(poll_id, voter_id)` prevents double-voting. See [01-data.md](01-data.md) for the full ERD, indexes, and cascade rules.

---

## phases

### phase 1 — data model (local) — **done**

- DDL for polls / options / votes (see [sql/](../sql/) and `app/flyway/sql/V1__initial_schema.sql`)
- postgres in docker, schema loaded via Flyway, tally query verified
- unique constraint rejects duplicates
- **done when:** manual `SELECT ... GROUP BY` returns correct counts ✔

### phase 2 — backend (python, local) — **done**

- FastAPI app with 5 endpoints + `/healthz` + `/readyz`
- SQLAlchemy models, Pydantic schemas
- **Flyway** for migrations (not Alembic) — same SQL used everywhere
- env-var config via `pydantic-settings`
- pytest + httpx against a real `voting_test` postgres db
- **done when:** two `X-User-Id`s can vote, tally is correct ✔

### phase 3 — containerize — **done**

- multi-stage Dockerfile, `python:3.12-slim`, non-root user
- `docker-compose.yml`: postgres + flyway (migrate) + flyway-test + api
- image pushed to Docker Hub (`simonangelfong/voting-api:0.1.0` / `:latest`)
- **done when:** fresh clone → `docker compose up` → working ✔

### phase 4 — helm chart (local cluster) — **done**

Chart lives at [helm/voting-app/](../helm/voting-app/). Full breakdown in [03-helm.md](03-helm.md).

- kind used as the target
- templates: app Deployment + Service, postgres StatefulSet + headless Service, ConfigMap + Secrets, **Gateway API `Gateway` + `HTTPRoute`** (nginx-gateway-fabric locally)
- Flyway runs as an **initContainer**; `V*.sql` packaged into a ConfigMap via `.Files.Glob "flyway-sql/*.sql"`
- `values-dev.yaml` (kind) / `values-prod.yaml` (EKS-shaped, `aws-alb` GatewayClass, external Gateway)
- `helm test` hits `/readyz`
- chart tagged `chart-v0.2.0`, milestone `v0.2.0`
- **done when:** `helm install` deploys, data survives pod restart, `helm test` passes, `values-prod.yaml` renders cleanly ✔

### phase 5 — CI + registry — **next**

- move image from Docker Hub → ECR (needed for EKS pull path)
- github actions on push to `master`: build → tag `${sha}` → push
- no `:latest` (ArgoCD needs immutable tags)
- **done when:** merge to `master` produces new image in ECR

### phase 6 — EKS cluster (terraform)

- layout:
  ```
  terraform/
    vpc.tf  eks.tf  iam.tf  addons.tf
    storageclass.tf  versions.tf
    variables.tf  outputs.tf  backend.tf
  ```
- modules: `terraform-aws-modules/vpc/aws`, `terraform-aws-modules/eks/aws`
- addons: EBS CSI driver (IRSA + `AmazonEBSCSIDriverPolicy`), **AWS Gateway API Controller** (matches `values-prod.yaml`), metrics-server
- `gp3` StorageClass, default, `WaitForFirstConsumer`, `allowVolumeExpansion: true`
- node group AZ-aligned with postgres PVC (EBS is zonal)
- state: S3 + DynamoDB lock
- **done when:** `kubectl get sc` shows `gp3 (default)`, a test PVC binds, Gateway API CRDs are present and `aws-alb` GatewayClass is `Accepted`

### phase 7 — ArgoCD

- install into `argocd` namespace
- `Application` manifest → helm chart in repo, using `values-prod.yaml`
- sync policy: automated + self-heal + prune
- platform team owns the `Gateway`; chart ships only `HTTPRoute` (`gateway.createGateway: false`)
- **done when:** commit to `values-prod.yaml` triggers a rollout, no manual `kubectl` needed

### phase 8 — observability + hardening

- `kube-prometheus-stack` via ArgoCD (Prometheus + Grafana)
- structured JSON logs → CloudWatch or Loki
- NetworkPolicies, PodSecurity, resource quotas
- postgres backup: `CronJob` running `pg_dump` → S3 (nightly)
- **done when:** dashboard shows RPS / errors / latency / DB conns, backup lands in S3

---

## persistence notes (in-cluster postgres)

- postgres = `StatefulSet`, single replica, `volumeClaimTemplate`
- PVC is zonal — pin node group / pod affinity to the volume's AZ
- start with 5Gi dev / 20Gi prod on `gp3`, expand later if needed
- backups are on us — no RDS snapshots; `pg_dump` CronJob is not optional

---

## guiding principles

1. every phase ends demoable — never break the working state
2. build inside-out: data → app → container → helm → CI → cluster → gitops → ops
3. commit at every "done when"
4. one source of truth for SQL — `app/flyway/sql/V*.sql` feeds compose + Helm ConfigMap
