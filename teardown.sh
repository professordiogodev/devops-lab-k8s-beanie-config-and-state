#!/usr/bin/env bash
# Removes the lab from your cluster and your folder. Run with: ./teardown.sh
set -u
cd "$(dirname "$0")"
kubectl cluster-info >/dev/null 2>&1 || { echo "kubectl cannot reach a cluster." >&2; exit 1; }
kubectl delete namespace beanie --ignore-not-found --wait=true --timeout=180s
pkill -f "port-forward.*-n beanie" 2>/dev/null
rm -rf beanie .image
echo "Now run ./verify-teardown.sh"
