---
title: Home
layout: default
---

# Multi-tenant Cluster with EKS

A multi-tenant EKS cluster that runs many teams on shared infrastructure. **Terraform** provisions AWS; **ArgoCD** runs everything above the API server via GitOps.

**AWS EKS · Terraform · ArgoCD · Karpenter · Istio (ambient) · AWS Load Balancer Controller · cert-manager · External Secrets · Kyverno**

---

## The idea in one paragraph

A small or mid-size enterprise with several product teams pays a heavy tax for per-team clusters — cost, upgrades, and governance all multiply. This project delivers **one shared EKS cluster** with platform-owned guardrails (compute, storage, network, security) and tenant-owned workloads. A tenant onboards with **3 pieces of info and 1 JSON file**; GitOps handles namespace, `AppProject`, `ApplicationSet`, subdomain, TLS, and policy.

Source & README: [github.com/simonangel-fong/eks-multi-tenant-cluster](https://github.com/simonangel-fong/eks-multi-tenant-cluster)

---

## Tenant guides

Read to onboard an app.

- [Onboarding](tenant/onboarding.md)
- [Compute](tenant/compute.md) — request nodes by workload class.
- [Network](tenant/network.md) — expose a service via `HTTPRoute`.

## Platform runbooks

Read to operate a live cluster.

- [Compute](platform/compute.md) — Karpenter, NodePools, workload classes.
- [Storage](platform/storage.md) — EBS CSI, StorageClasses, tag-based cost attribution.
- [Networking](platform/networking.md) — Gateway API, Istio ambient, ALBC, external-dns.
- [Security](platform/security.md) — ESO, cert-manager, Kyverno, isolation model.
- [Onboarding a tenant](platform/onboarding.md) — the single-file PR flow.

## Design & implementation

Read to understand how the project is built.

- [IaC with Terraform](dev/01-infra.md)
- [GitOps with ArgoCD](dev/02-argocd.md) — repo layout + sync-wave order.
- [Capabilities](dev/03-capabilities.md)
