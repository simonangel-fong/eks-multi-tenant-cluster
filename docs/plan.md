project: voting system — plan

---

## scope

- single voting service (polls, votes, results in one app)
- postgres in-cluster (no RDS), persisted via EBS CSI
- no auth for now — trust `X-User-Id` header (swap to Cognito later)
- deployed to EKS via ArgoCD (GitOps)

---

## stack

- backend: python — FastAPI, SQLAlchemy, Alembic, psycopg
- db: postgres 16
- container: docker (multi-stage, non-root)
- k8s: EKS, Helm chart, ArgoCD
- iac: terraform (VPC, EKS, IRSA, addons)
- ci: github actions → ECR

---

## repo layout

```
project-eks-argocd/
├─ .github/            # CI workflows (build/push image, terraform plan)
├─ app/                # python backend
│  ├─ voting/          # FastAPI source
│  ├─ tests/           # pytest
│  ├─ Dockerfile       # multi-stage, non-root
│  └─ pyproject.toml
├─ helm/               # helm chart — single source of truth for k8s manifests
├─ argocd/             # Application manifests (GitOps entry points)
├─ terraform/          # EKS, VPC, IRSA, addons, gp3 StorageClass
├─ docs/               # design, plan, ADRs
├─ scripts/            # small dev helpers (psql, port-forward)
├─ sql/                # seed data for local dev
└─ docker-compose.yml  # local dev stack (app + postgres)
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

---

## schema

```sql
polls    (id, title, created_at, closes_at)
options  (id, poll_id, label)
votes    (id, poll_id, option_id, voter_id, created_at,
          UNIQUE(poll_id, voter_id))
```

`UNIQUE(poll_id, voter_id)` prevents double-voting.

---

## phases

### phase 1 — data model (local)

- write DDL for polls / options / votes
- run postgres in docker, load schema, test tally query
- confirm unique constraint rejects duplicates
- **done when:** manual `SELECT ... GROUP BY` returns correct counts

### phase 2 — backend (python, local)

- FastAPI app with 5 endpoints + `/healthz` + `/readyz`
- SQLAlchemy models, Pydantic schemas, Alembic migration `0001`
- env-var config via `pydantic-settings`
- pytest + httpx for endpoint tests
- **done when:** two `X-User-Id`s can vote, tally is correct

### phase 3 — containerize

- multi-stage Dockerfile, `python:3.12-slim`, non-root user
- `docker-compose.yml`: app + postgres, alembic runs on startup
- **done when:** fresh clone → `docker compose up` → working

### phase 4 — helm chart (local cluster)

- kind/minikube for the target
- `helm/voting-app/` — templates: app Deployment + Service + Ingress, postgres StatefulSet + PVC, ConfigMap + Secret
- alembic as initContainer
- `values.yaml`: image tag, replicas, DB creds, storage size, storageClass, ingress host, resources
- `values-dev.yaml` / `values-prod.yaml` overlays
- **done when:** `helm install` deploys to local cluster, data survives pod restart, same chart works with two value files

### phase 5 — CI + registry

- push images to ECR
- github actions on push to `main`: build → tag `${sha}` → push
- no `:latest` (ArgoCD needs immutable tags)
- **done when:** merge to main produces new image in ECR

### phase 6 — EKS cluster (terraform)

- layout:
  ```
  terraform/
    vpc.tf  eks.tf  iam.tf  addons.tf
    storageclass.tf  versions.tf
    variables.tf  outputs.tf  backend.tf
  ```
- modules: `terraform-aws-modules/vpc/aws`, `terraform-aws-modules/eks/aws`
- addons: EBS CSI driver (IRSA + `AmazonEBSCSIDriverPolicy`), AWS Load Balancer Controller, metrics-server
- `gp3` StorageClass, default, `WaitForFirstConsumer`, `allowVolumeExpansion: true`
- node group AZ-aligned with postgres PVC (EBS is zonal)
- state: S3 + DynamoDB lock
- **done when:** `kubectl get sc` shows `gp3 (default)` and a test PVC binds

### phase 7 — ArgoCD

- install into `argocd` namespace
- `Application` manifest → helm chart in repo
- sync policy: automated + self-heal + prune
- **done when:** commit to `values.yaml` triggers a rollout, no manual `kubectl` needed

### phase 8 — observability + hardening

- `kube-prometheus-stack` via ArgoCD (Prometheus + Grafana)
- structured JSON logs → CloudWatch or Loki
- NetworkPolicies, PodSecurity, resource quotas
- postgres backup: `CronJob` running `pg_dump` → S3 (nightly)
- **done when:** dashboard shows RPS / errors / latency / DB conns, backup lands in S3

---

## persistence notes (in-cluster postgres)

- postgres = `StatefulSet`, single replica, one PVC
- PVC is zonal — pin node group / pod affinity to the volume's AZ
- start with 10–20Gi on `gp3`, expand later if needed
- backups are on us — no RDS snapshots; `pg_dump` CronJob is not optional

---

## guiding principles

1. every phase ends demoable — never break the working state
2. build inside-out: data → app → container → helm → CI → cluster → gitops → ops
3. commit at every "done when"
