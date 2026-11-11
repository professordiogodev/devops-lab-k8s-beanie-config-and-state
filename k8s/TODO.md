# What to write in this folder

`k8s/base/` is a working Beanie (the result of the previous lab). `orders` already runs **2 replicas**, with no database: that is the problem you will see in Part 1.

You write, one file each, next to `base/`:

| File | What |
|------|------|
| `config.yaml` | A ConfigMap `beanie-config` with `LOG_LEVEL`, `LOG_FORMAT`, `DOWNSTREAM_TIMEOUT`, `MAX_ITEMS_PER_ORDER` |
| `postgres.yaml` | A **StatefulSet** `postgres` (image `postgres:16`), a **headless** Service `postgres`, and a `volumeClaimTemplates` entry of 1Gi |

The **Secret** is NOT a file in git. You create it from the command line (Part 3).

Then edit `base/orders.yaml` (the TODO comments at the top).
