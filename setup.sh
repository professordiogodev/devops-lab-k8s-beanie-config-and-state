#!/usr/bin/env bash
# Gets Beanie, builds its image and makes it available to your local cluster. Run: ./setup.sh
# Using an image that already exists (for example in a registry)?  BEANIE_IMAGE=registry/beanie:0.1.0 ./setup.sh
set -u
cd "$(dirname "$0")"
for c in kubectl git curl python3; do command -v "$c" >/dev/null || { echo "MISSING: $c"; exit 1; }; done
kubectl cluster-info >/dev/null 2>&1 || { echo "kubectl cannot reach a cluster. Start kind, OrbStack or Docker Desktop Kubernetes and check: kubectl get nodes"; exit 1; }
CTX=$(kubectl config current-context)
echo "kubectl context: $CTX"
if [ ! -d beanie ]; then
  echo "Getting Beanie (v0.1.0)..."
  git clone -q -c advice.detachedHead=false --depth 1 --branch v0.1.0 https://github.com/professordiogodev/beanie.git beanie || { echo "could not clone beanie"; exit 1; }
fi
if [ -n "${BEANIE_IMAGE:-}" ]; then
  IMG=$BEANIE_IMAGE
  echo "Using the image you gave: $IMG"
else
  command -v docker >/dev/null || { echo "MISSING: docker"; exit 1; }
  docker info >/dev/null 2>&1 || { echo "Docker is not running."; exit 1; }
  IMG=beanie:0.1.0
  echo "Building $IMG ..."
  docker build -q -t "$IMG" . >/dev/null || { echo "image build failed"; exit 1; }
  case "$CTX" in
    kind-*)
      command -v kind >/dev/null || { echo "MISSING: kind"; exit 1; }
      echo "kind cluster: loading the image into it..."
      kind load docker-image "$IMG" --name "${CTX#kind-}" >/dev/null || { echo "kind load failed"; exit 1; } ;;
    orbstack|docker-desktop|docker-for-desktop|rancher-desktop|minikube) : ;;
    *) echo "WARNING: '$CTX' is not a local cluster I recognise. The nodes must be able to pull $IMG; push it to a registry and run again with BEANIE_IMAGE=..." ;;
  esac
fi
echo "$IMG" > .image
echo
echo "Ready. In your manifests use:   image: $IMG"
echo "Cluster nodes:"; kubectl get nodes
