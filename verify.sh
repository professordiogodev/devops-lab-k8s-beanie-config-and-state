#!/usr/bin/env bash
# Reads your manifests, your cluster, and then breaks things on purpose. Run with: ./verify.sh
cd "$(dirname "$0")" || exit 1
command -v kubectl >/dev/null || { echo "kubectl is not installed." >&2; exit 1; }
kubectl cluster-info >/dev/null 2>&1 || { echo "kubectl cannot reach a cluster." >&2; exit 1; }
[ -f .image ] || { echo "Run ./setup.sh first." >&2; exit 1; }
exec python3 .lab/k8scheck.py
