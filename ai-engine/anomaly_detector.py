import requests
import pandas as pd
import time
import subprocess
from datetime import datetime
from sklearn.ensemble import IsolationForest

# ========================
# CONFIGURATION
# ========================

PROMETHEUS_URL = "http://localhost:9090"
NAMESPACE = "aegisops"
DEPLOYMENT_NAME = "aegisops-app"

BASELINE_SAMPLES = 30
BASELINE_INTERVAL = 5          # seconds
MONITOR_INTERVAL = 10          # seconds
COOLDOWN_SECONDS = 120         # prevent restart loops

QUERIES = {
    "rps": 'rate(http_requests_total[1m])',
    "latency_p95": '''
        histogram_quantile(
          0.95,
          rate(http_request_latency_seconds_bucket[1m])
        )
    ''',
    "memory": "process_resident_memory_bytes"
}

# ========================
# PROMETHEUS QUERY
# ========================

def query_prometheus(query):
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": query},
        timeout=5
    )

    results = response.json().get("data", {}).get("result", [])

    cleaned = []
    for r in results:
        try:
            v = float(r["value"][1])
            if pd.notna(v) and v != float("inf"):
                cleaned.append(v)
        except Exception:
            continue

    return sum(cleaned) / len(cleaned) if cleaned else 0.0


def collect_metrics():
    return {
        "rps": query_prometheus(QUERIES["rps"]),
        "latency_p95": query_prometheus(QUERIES["latency_p95"]),
        "memory": query_prometheus(QUERIES["memory"])
    }

# ========================
# KUBERNETES AUTO-HEALING
# ========================

def restart_kubernetes_deployment():
    print("🔧 Triggering Kubernetes auto-healing (rollout restart)")

    try:
        subprocess.run(
            [
                "kubectl",
                "rollout",
                "restart",
                f"deployment/{DEPLOYMENT_NAME}",
                "-n",
                NAMESPACE
            ],
            check=True
        )
        print("✅ Deployment restart triggered successfully")

    except subprocess.CalledProcessError as e:
        print("❌ Failed to restart deployment:", e)

# ========================
# MAIN AIOPS LOOP
# ========================

def main():
    print("\n📊 Collecting baseline metrics...\n")

    baseline_data = []

    for _ in range(BASELINE_SAMPLES):
        metrics = collect_metrics()

        # Skip cold-start samples
        if metrics["rps"] == 0.0 and metrics["latency_p95"] == 0.0:
            print("⏭ Skipping cold-start sample:", metrics)
        else:
            baseline_data.append(metrics)
            print("📈 Baseline:", metrics)

        time.sleep(BASELINE_INTERVAL)

    if len(baseline_data) < 10:
        raise RuntimeError(
            "❌ Not enough baseline data. Generate traffic and restart detector."
        )

    df_baseline = pd.DataFrame(baseline_data)

    model = IsolationForest(
        contamination=0.15,
        random_state=42
    )
    model.fit(df_baseline)

    print("\n✅ Baseline trained successfully")
    print("🚦 Monitoring for anomalies...\n")

    last_remediation_time = None

    while True:
        metrics = collect_metrics()
        df_current = pd.DataFrame([metrics])
        prediction = model.predict(df_current)[0]

        # No traffic → do nothing
        if metrics["rps"] == 0.0:
            print("⏸ No traffic — skipping detection", metrics)

        # Anomaly detected
        elif prediction == -1:
            now = time.time()

            if (
                last_remediation_time is None
                or now - last_remediation_time > COOLDOWN_SECONDS
            ):
                print("🚨 ANOMALY DETECTED", metrics)

                restart_kubernetes_deployment()
                last_remediation_time = now

                print(
                    f"📝 Remediation executed at "
                    f"{datetime.now().isoformat()}\n"
                )
            else:
                print(
                    "⏳ Anomaly detected but cooldown active — "
                    "skipping remediation"
                )

        # Normal behaviour
        else:
            print("✅ Normal", metrics)

        time.sleep(MONITOR_INTERVAL)

# ========================
# ENTRYPOINT
# ========================

if __name__ == "__main__":
    main()