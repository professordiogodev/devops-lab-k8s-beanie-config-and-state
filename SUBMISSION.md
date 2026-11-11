# Submission

Fork URL: <!-- paste the URL of your fork here -->

## Files to commit

- [ ] `k8s/` with your manifests (ConfigMap, Secret created from the command line, PostgreSQL StatefulSet with a PVC, the updated Deployments)
- [ ] `notes.md` with your commands and what you saw (optional)

## Questions

Answer in your own words. Where a question asks for output, paste it in a code block.

### Q1. Before the fix: paste two `GET /api/orders` answers taken from two different orders pods. Why do they differ, and why does the README say a database is the lesson?

**Your answer:**

<!-- replace this line with your answer -->

### Q2. Paste your ConfigMap and say which values you moved there. Why is the database URL not in it?

**Your answer:**

<!-- replace this line with your answer -->

### Q3. The database password: how did you create the Secret without writing the password in a file you commit? Is a Secret encrypted? Say what base64 does and does not do, and name one way to do better in a real cluster.

**Your answer:**

<!-- replace this line with your answer -->

### Q4. Paste `kubectl get pvc,pv,statefulset -n beanie`. Delete the PostgreSQL pod, wait for it to come back, and paste an order placed before the deletion. What object kept the data and what would happen to it if you deleted the StatefulSet? The PVC?

**Your answer:**

<!-- replace this line with your answer -->

### Q5. Why did you use a StatefulSet and not a Deployment for PostgreSQL? Name two guarantees it gives that a Deployment does not.

**Your answer:**

<!-- replace this line with your answer -->

### Q6. Change a value in the ConfigMap. Do the running pods see it? What did you have to do and how would you automate it?

**Your answer:**

<!-- replace this line with your answer -->

### Q7. Paste the output of `./verify.sh`. It must end with **ALL CHECKS PASSED**.

**Your answer:**

<!-- replace this line with your answer -->

### Q8. **Tear down.** Paste the output of `./verify-teardown.sh`. It must end with **TEARDOWN VERIFIED**.

**Your answer:**

<!-- replace this line with your answer -->
