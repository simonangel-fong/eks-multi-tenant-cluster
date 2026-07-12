# Multi-tenant Platform Runbook - Tenant Onboarding

[Back](../../README.md)

- [Multi-tenant Platform Runbook - Tenant Onboarding](#multi-tenant-platform-runbook---tenant-onboarding)
  - [Overview](#overview)
  - [Intake](#intake)
  - [Onboarding Steps](#onboarding-steps)
  - [What the Blueprint Renders](#what-the-blueprint-renders)
  - [Verification](#verification)
  - [Offboarding](#offboarding)
  - [Common Issues](#common-issues)

---

## Overview

Onboarding is a single-file PR. Adding one JSON file under `tenants/` triggers the `tenants` ApplicationSet ([argocd/platform-init/tenants-appset.yaml](../../argocd/platform-init/tenants-appset.yaml)), which renders a per-tenant Argo CD `Application` (`tenant-<name>`) that:

1. **Provisions namespace + guardrails** from [tenant-chart/](../../tenant-chart/) — namespace, `PeerAuthentication`, `NetworkPolicy` (default-deny + platform-ingress allow), `ResourceQuota`, `LimitRange`, tenant `AppProject`.
2. **Syncs the tenant's workload manifests** from the path they specify (`manifestPath` in their JSON).

Both are handled by a single Argo CD Application per tenant using multi-source (`spec.sources`) — no nested Applications, no finalizer races.

Reference: [tenants/team-a.json](../../tenants/team-a.json).

---

## Intake

Collect from the tenant before opening the PR:

| Field                | Example                                                       | Used for                            |
| -------------------- | ------------------------------------------------------------- | ----------------------------------- |
| Team name (`<team>`) | `team-a`                                                      | namespace, subdomain, `team` label  |
| Source repo          | `https://github.com/simonangel-fong/eks-multi-tenant-cluster` | `AppProject.sourceRepos`            |
| Manifests path       | `demo-app/team-a` or `demo-app/team-b/chart`                  | `Application.spec.sources[1].path`  |
| AWS access?          | which secrets / S3 buckets                                    | Pod Identity role provisioning      |

Quota, tier, IAM overrides are not yet part of the schema — the blueprint uses fixed baseline values. Extend `tenant-chart/values.yaml` and `tenants/*.json` when needed.

---

## Onboarding Steps

1. **Open a PR** adding one file: `tenants/<team>.json`.

   ```json
   {
     "name": "team-a",
     "sourceRepo": "https://github.com/simonangel-fong/eks-multi-tenant-cluster",
     "manifestPath": "demo-app/team-a"
   }
   ```

   `manifestPath` can point at a plain-manifest directory or a Helm chart directory (auto-detected by Argo).

2. **Provision AWS prerequisites** (if requested) via Terraform: Pod Identity role, ASM secret paths, S3 buckets.
3. **Update `CODEOWNERS`** so `demo-app/<team>/` (or the tenant's manifest path) requires the dev team's review.
4. **Merge to `master`.** The `tenants` ApplicationSet reconciles within ~60s and generates `tenant-<team>`.
5. **Confirm sync** — see [Verification](#verification).

The tenant then opens their own PR against their manifests path. See [../tenant/onboarding.md](../tenant/onboarding.md) for the tenant-facing flow.

---

## What the Blueprint Renders

The Argo CD Application `tenant-<team>` has two sources:

- **Source 1** — [tenant-chart/](../../tenant-chart/): renders the platform-owned guardrails.
- **Source 2** — the tenant's `manifestPath`: renders the tenant's workload.

Both sources target `destination.namespace: <team>`. Resources with explicit `metadata.namespace` (`AppProject` → `argocd`) override the default.

### 1. Namespace — ambient mesh enrollment + team label

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: <team>
  labels:
    team: <team>
    istio.io/dataplane-mode: ambient # ztunnel takes over; no sidecars
```

### 2. `PeerAuthentication` — refuse plaintext peers

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata: { name: default, namespace: <team> }
spec:
  mtls: { mode: STRICT }
```

### 3. NetworkPolicy — default-deny + platform-ingress allow

Ships as two policies: a blanket `default-deny` and a companion `allow-platform-ingress-and-dns` that restores the paths the platform needs. **Every rule matters** — omitting one breaks day-one traffic:

| Rule                               | Why                                                                                     |
| ---------------------------------- | --------------------------------------------------------------------------------------- |
| Ingress from `istio-ingress` ns    | Shared Gateway → tenant pods                                                            |
| Ingress from `istio-system` ns     | ztunnel / waypoint HBONE                                                                |
| Ingress from `169.254.7.127/32`    | **Ambient SNATs kubelet probes to this link-local** — without this, all probes time out |
| Ingress from `10.0.0.0/16`         | Non-ambient probe path (fallback if a pod exits ambient)                                |
| Ingress on TCP 15008 from any ns   | HBONE — east-west ambient mTLS tunnel                                                   |
| Egress UDP/TCP 53 → `kube-system`  | DNS                                                                                     |
| Egress to `istio-system`           | ztunnel xDS + upstream to waypoints                                                     |
| Egress to any pod in the namespace | Internal traffic                                                                        |

### 4. Baseline `ResourceQuota` + `LimitRange`

Defaults from [tenant-chart/values.yaml](../../tenant-chart/values.yaml):

| Field                     | Value            |
| ------------------------- | ---------------- |
| `requests.cpu`            | `4`              |
| `requests.memory`         | `8Gi`            |
| `limits.cpu`              | `8`              |
| `limits.memory`           | `16Gi`           |
| `persistentvolumeclaims`  | `10`             |
| Container default request | `100m` / `128Mi` |
| Container default limit   | `500m` / `512Mi` |

### 5. Tenant `AppProject`

Named `<team>`, whitelists two source repos (the platform repo for the blueprint chart + the tenant's own `sourceRepo`), destination locked to namespace `<team>`, cluster-scoped resources denied.

---

## Verification

```sh
# 1. Application exists and is healthy
argocd app get tenant-<team>
kubectl -n argocd get appproject <team>

# 2. Namespace guardrails applied
kubectl get ns <team> --show-labels                    # team=<team>, istio.io/dataplane-mode=ambient
kubectl -n <team> get peerauthentication,networkpolicy,resourcequota,limitrange

# 3. Ambient mesh has picked up the namespace
istioctl ztunnel-config workloads | grep <team>

# 4. Tenant workload smoke test
kubectl -n <team> get pods,svc,httproute
curl -I https://<team>.arguswatcher.net                # expect 200/301, valid TLS cert
```

---

## Offboarding

```sh
git rm tenants/<team>.json
git commit -m "offboard <team>"
git push
```

The ApplicationSet detects the removal, deletes `tenant-<team>`, and cascades through the namespace and workloads. No manual finalizer patching is required. Complete within ~60s.

---

## Common Issues

| Symptom                                                               | Likely cause                                                             | Fix                                                                                                |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| Tenant `Application` stuck `Unknown`                                  | `AppProject` `sourceRepos` or `destinations` don't match the Application | Align repo URL and namespace between `AppProject` and `Application`.                               |
| Kyverno rejects tenant workloads (`require-team-label`, etc.)         | Manifests missing `team` label, requests, probes, or use `:latest`       | Point the tenant at the Kyverno policy list ([06-security.md](06-security.md#kyverno-policy-set)). |
| All pods time out on probes right after onboarding                    | NetworkPolicy missing the `169.254.7.127/32` ambient-SNAT rule           | Re-apply `allow-platform-ingress-and-dns` from the reference manifest.                             |
| East-west traffic silently dropped between two ambient namespaces     | HBONE (TCP 15008) not allowed in tenant NetworkPolicy                    | Add the `port: 15008` ingress rule.                                                                |
| Tenant hits quota on first deploy                                     | Baseline quota too tight for the workload                                | Extend `tenant-chart/values.yaml` schema to allow per-tenant overrides.                            |
| `HTTPRoute` rejected by Kyverno (`httproute-hostname-scoped-to-team`) | Hostname not under `<team>.arguswatcher.net`                             | Tenant must use their subdomain, or platform adds a custom listener + cert.                        |
| Offboard leaves stuck Application                                     | Manual `argocd app delete` bypassed the ApplicationSet                   | Always offboard via `git rm tenants/<team>.json`, not `argocd app delete`.                         |
