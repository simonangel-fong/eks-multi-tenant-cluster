# Tenancy contract

What a workload team gets when onboarded, what they can do with it,
and what stays platform-owned.

## What a team gets

Per team:

- **ArgoCD `AppProject`** — scoped to their namespaces and their subdomain
- **Grafana folder** — `Team: <Team>` with edit access (once SSO is wired)
- **Alertmanager routes** — `#<team>-alerts` for warnings, `#<team>-oncall` for critical

Per environment (`<team>-dev`, `<team>-prod`):

- **Namespace** enrolled in the ambient mesh, PSA `restricted`
- **ResourceQuota** — CPU/memory/pod/PVC/service caps
- **LimitRange** — sensible defaults for containers without explicit resources
- **RoleBinding** to team's OIDC group (edit in dev, view in prod)
- **NetworkPolicy** — default-deny with explicit allows for platform ingress + DNS + egress

## What a team can do

- Deploy `Deployment`, `StatefulSet`, `Service`, `HTTPRoute`, `ExternalSecret`, `ServiceMonitor`, `PrometheusRule`, `Rollout`, `ConfigMap`, `Secret`, `Job`, `CronJob`, `PersistentVolumeClaim` in their namespaces
- Claim HTTPRoute hostnames under `<team>.arguswatcher.net`
- Reference platform `ClusterAnalysisTemplate`s from Rollouts
- Commit dashboards as ConfigMaps into their Grafana folder
- Ship PrometheusRules labeled `team: <team>` — auto-routed to their Slack

## What a team cannot do

Enforced by AppProject + Kyverno + RBAC:

- **Cluster-scoped resources** — no `Namespace`, no `ClusterRole`, no `Gateway`, no `ClusterIssuer`
- **Other teams' namespaces** — RBAC scoped to their own
- **Platform namespaces** — no access
- **Non-team hostnames** — Kyverno rejects `HTTPRoute` outside their subdomain
- **`:latest` images, missing probes, missing resource requests, host namespaces, privileged containers** — Kyverno rejects at admission
- **Alertmanager config** — teams ship `AlertmanagerConfig` CRs in `monitoring`; platform-managed operator merges them

## Guarantees

- **Namespaces are never pruned** without explicit platform-team action, even if the team chart is removed
- **Quotas are negotiable** — bump via a PR to the tenant Application values
- **RBAC follows GitHub team membership** — leaving the team removes access on next login
- **Kyverno policy changes are announced** — a platform-team PR before enforcement changes

## Ownership boundary

**Platform team owns:** tenancy primitive (`helm/team`, `helm/team-namespace`),
policies, capabilities. On-call for the platform itself.

**Workload team owns:** their apps, their dashboards, their alerts, their SLOs,
their on-call for their services. Their `HTTPRoute`, `ServiceMonitor`,
`PrometheusRule`, `Rollout` resources live in their app repo.

## Roadmap

- OIDC group binding once SSO is wired (Phase 1g roadmap)
- Strict declared egress (currently permissive to 443)
- Per-team PodDisruptionBudget defaults
- Cost allocation reports by team label (OpenCost)
