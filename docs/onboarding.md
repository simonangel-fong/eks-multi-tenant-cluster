# Onboarding a new team

Zero to first HTTPRoute serving traffic. Platform team steps 1–4;
team steps 5–10.

## Prerequisites

- Team lead identified
- Team name chosen (short, kebab-case; used as namespace prefix and subdomain)
- Team's Slack channels created: `#<team>-alerts`, `#<team>-oncall`
- (Once SSO is wired) GitHub team `<team>-devs` created in the org

## Platform team steps

**1. Create the team-level Application.**

`argocd/tenants/<team>.yaml` — one ArgoCD Application referencing
`helm/team` with team values:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: tenant-<team>
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/simonangel-fong/project-eks-argocd
    targetRevision: master
    path: helm/team
    helm:
      values: |
        team: <team>
        subdomain: <team>.arguswatcher.net
        slack:
          alerts: "#<team>-alerts"
          oncall: "#<team>-oncall"
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated: {prune: true, selfHeal: true}
    syncOptions: [ServerSideApply=true]
```

**2. Create the per-environment Applications.**

`argocd/tenants/<team>-dev.yaml` and `argocd/tenants/<team>-prod.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: tenant-<team>-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/simonangel-fong/project-eks-argocd
    targetRevision: master
    path: helm/team-namespace
    helm:
      values: |
        team: <team>
        environment: dev
        rbac:
          clusterRole: edit
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated: {prune: true, selfHeal: true}
    syncOptions: [ServerSideApply=true]
```

Prod overlay differs on `environment: prod`, `rbac.clusterRole: view`,
and typically larger quotas.

**3. Merge the PR.**

ArgoCD picks up the new tenants Applications on next reconcile.

**4. Verify.**

```powershell
kubectl get ns <team>-dev <team>-prod
kubectl get resourcequota,limitrange,networkpolicy -n <team>-dev
kubectl get appproject <team> -n argocd
kubectl get alertmanagerconfig -n monitoring | Select-String <team>
```

Then hand off to the team with a pointer to `workload-contract.md`.

## Team steps

**5. Create the app repo.**

Follow `docs/workload-contract.md` for required labels, endpoints,
resource requests, probes.

**6. Ship an ArgoCD Application** pointing at your Helm chart, targeting
your namespace, project `<team>`.

**7. Add HTTPRoute** for `<yourapp>.<team>.arguswatcher.net` on the
shared Istio Gateway.

**8. Ship metrics.** Add `/metrics` endpoint, a `ServiceMonitor`, and
`PrometheusRule` labeled `team: <team>` with `runbook_url` annotations.

**9. Commit dashboards** as ConfigMaps labeled `grafana_dashboard: "1"`,
annotated `grafana_folder: "Team: <Team>"`.

**10. Push.**

ArgoCD syncs, external-dns creates the CNAME, cert-manager's wildcard
covers your hostname, alerts route to your Slack, dashboards appear in
your Grafana folder.

## Time budget

- Platform team steps 1–4: **~15 minutes**
- Team steps 5–10: **1–2 hours** depending on app complexity
- Total: same-day onboarding

## Offboarding

Delete the three tenant Applications. Namespaces are annotated
`Prune=false` — they survive until manually removed:

```powershell
kubectl delete ns <team>-dev <team>-prod
```
