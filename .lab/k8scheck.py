#!/usr/bin/env python3
import base64, glob, json, os, re, socket, subprocess, sys, time, urllib.request, urllib.error
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
NS = "beanie"
passed = failed = 0


def check(desc, ok, hint=""):
    global passed, failed
    if ok:
        passed += 1; print("PASS  " + desc)
    else:
        failed += 1; print("FAIL  " + desc + (("   -> " + hint) if hint else ""))


def k(*a, timeout=120):
    r = subprocess.run(("kubectl",) + a, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def kj(*a):
    rc, out, _ = k(*a, "-o", "json")
    try:
        return json.loads(out) if rc == 0 else None
    except Exception:
        return None


def finish():
    print()
    print(("ALL CHECKS PASSED (%d/%d)" % (passed, passed)) if failed == 0 else ("%d check(s) failed, %d passed" % (failed, passed)))
    sys.exit(1 if failed else 0)


def wait_for(fn, secs, step=3):
    end = time.time() + secs
    while time.time() < end:
        if fn():
            return True
        time.sleep(step)
    return False


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def http(url, data=None, timeout=10):
    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception:
        return 0, ""


print("kubectl context: " + k("config", "current-context")[1].strip())
print("== Nothing secret in git ==")
files = [f for f in glob.glob("k8s/**/*", recursive=True) if os.path.isfile(f)]
txt = "\n".join(open(f).read() for f in files if f.endswith((".yaml", ".yml")))
code = "\n".join(l for l in txt.split("\n") if not l.lstrip().startswith("#"))
check("no `kind: Secret` manifest in k8s/ (a Secret in git is a leaked secret)", not re.search(r"^kind:\s*Secret\s*$", code, re.M))
check("no password written into a database URL or POSTGRES_PASSWORD value in k8s/", not re.search(r"postgres(ql)?://[^:@\s]+:(?!\$\()[^@\s]+@", code) and not re.search(r"POSTGRES_PASSWORD\s*\n?\s*(value|-\s*value):", code))

print("== Configuration ==")
cms = (kj("get", "configmaps", "-n", NS) or {}).get("items", [])
cm = next((c for c in cms if c["metadata"]["name"] == "beanie-config"), None)
check("ConfigMap beanie-config exists with LOG_LEVEL, LOG_FORMAT, DOWNSTREAM_TIMEOUT, MAX_ITEMS_PER_ORDER", bool(cm) and {"LOG_LEVEL", "LOG_FORMAT", "DOWNSTREAM_TIMEOUT", "MAX_ITEMS_PER_ORDER"} <= set(cm.get("data", {})), "kubectl apply -f k8s/config.yaml")
deps = {d["metadata"]["name"]: d for d in (kj("get", "deployments", "-n", NS) or {}).get("items", [])}
o = deps.get("orders", {}).get("spec", {}).get("template", {}).get("spec", {}).get("containers", [{}])[0]
check("orders takes its settings from the ConfigMap (envFrom or configMapKeyRef)", any(e.get("configMapRef", {}).get("name") == "beanie-config" for e in o.get("envFrom", [])) or any(e.get("valueFrom", {}).get("configMapKeyRef") for e in o.get("env", [])))

print("== The Secret and the database ==")
sec = kj("get", "secrets", "-n", NS) or {}
user_secrets = [s for s in sec.get("items", []) if s.get("type") == "Opaque"]
pw = ""
for s in user_secrets:
    for key, val in (s.get("data") or {}).items():
        if "PASSWORD" in key.upper():
            pw = base64.b64decode(val).decode()
check("a Secret with a password exists in the cluster, created from the command line", bool(pw))
check("the password is not a guessable default (12+ characters, not 'postgres' or 'password')", len(pw) >= 12 and pw.lower() not in ("postgres", "password"))
sts = (kj("get", "statefulset", "postgres", "-n", NS) or {})
check("postgres is a StatefulSet with a volumeClaimTemplate", bool(sts) and bool(sts.get("spec", {}).get("volumeClaimTemplates")))
svc = kj("get", "service", "postgres", "-n", NS) or {}
check("the postgres Service is headless (clusterIP: None) and not exposed outside", svc.get("spec", {}).get("clusterIP") == "None" and svc.get("spec", {}).get("type", "ClusterIP") == "ClusterIP")
pvcs = (kj("get", "pvc", "-n", NS) or {}).get("items", [])
check("a PersistentVolumeClaim is Bound", any(p["status"].get("phase") == "Bound" for p in pvcs), "kubectl get pvc -n beanie; storage class?")
check("postgres takes its password from the Secret (secretKeyRef), not from a literal", any("secretKeyRef" in json.dumps(e) for e in sts.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [{}])[0].get("env", [])))
envs = o.get("env", [])
dburl = next((e for e in envs if e["name"] == "DATABASE_URL"), None)
check("orders has DATABASE_URL built from the Secret ($(VAR) of a secretKeyRef variable), or itself from a Secret", bool(dburl) and ("valueFrom" in dburl or ("$(" in dburl.get("value", "") and any(x.get("valueFrom", {}).get("secretKeyRef") for x in envs))))
ready = wait_for(lambda: all((kj("get", "deployment", n, "-n", NS) or {}).get("status", {}).get("readyReplicas", 0) >= deps[n]["spec"]["replicas"] for n in deps) and (kj("get", "statefulset", "postgres", "-n", NS) or {}).get("status", {}).get("readyReplicas", 0) >= 1, 180)
check("everything is Ready, orders runs 2 replicas or more", ready and deps.get("orders", {}).get("spec", {}).get("replicas", 0) >= 2, "kubectl get pods -n beanie")
if not ready:
    finish()

print("== Live ==")
port = free_port()
pf = subprocess.Popen(["kubectl", "port-forward", "-n", NS, "svc/gateway", "%d:8000" % port], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
base = "http://127.0.0.1:%d" % port
try:
    wait_for(lambda: http(base + "/healthz")[0] == 200, 20, 1)
    ids = []
    for i in range(8):
        st, body = http(base + "/api/orders", json.dumps({"customer": "Cust%d" % i, "items": [{"item_id": "flat-white", "quantity": 1}]}).encode())
        try:
            ids.append(json.loads(body)["id"])
        except Exception:
            pass
    check("8 orders placed through the gateway (201)", len(ids) == 8)
    seen = set()
    for _ in range(12):
        st, body = http(base + "/api/orders")
        try:
            seen.add(len(json.loads(body)))
        except Exception:
            seen.add(-1)
    check("every request to GET /api/orders sees the same 8+ orders, whichever orders pod answers (shared database)", len(seen) == 1 and min(seen) >= 8, "counts seen: %s" % sorted(seen))
    k("delete", "pod", "postgres-0", "-n", NS, "--wait=false")
    time.sleep(3)
    back = wait_for(lambda: (kj("get", "statefulset", "postgres", "-n", NS) or {}).get("status", {}).get("readyReplicas", 0) >= 1, 150)
    check("the database pod was deleted and came back", back)
    def orders_after():
        st, body = http(base + "/api/orders")
        try:
            return {x["id"] for x in json.loads(body)}
        except Exception:
            return set()
    ok = wait_for(lambda: set(ids) <= orders_after(), 90)
    check("all 8 orders survived the deletion of the database pod (the volume kept the data)", ok)
    k("delete", "pods", "-n", NS, "-l", "app=orders", "--wait=false")
    time.sleep(3)
    ok2 = wait_for(lambda: (kj("get", "deployment", "orders", "-n", NS) or {}).get("status", {}).get("readyReplicas", 0) >= 2 and set(ids) <= orders_after(), 120)
    check("... and survived the deletion of every orders pod", ok2)
finally:
    pf.terminate()
finish()
