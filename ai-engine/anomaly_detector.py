import os
import time
import requests
import pandas as pd
from datetime import datetime
from sklearn.ensemble import IsolationForest

from kubernetes import client, config

# ========================
# CONFIGURATION
# ========================

PROMETHEUS_URL = (
    "http://monitoring-kube-prometheus-prometheus."
    "aegisops.svc.cluster.local:9090"
)

NAMESPACE = "aegisops"
DEPLOYMENT_NAME = "aegisops-app"

BASELINE_SAMPLES = 30
BASELINE_INTERVAL = 5      # seconds
MONITOR_INTERVAL = 10      # seconds
COOLDOWN_SECONDS = 120     # prevent scaling loops

SCALE_UP_REPLICAS = 4

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
# PROMETHEUS QUERY LOGIC
# ========================

def query_prometheus(query: str) -> float:
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query},
            timeout=5
        )
        response.raise_for_status()
    except Exception as e:
        print("❌ Prometheus query failed:", e)
        return 0.0

    results = response.json().get("data", {}).get("result", [])

    values = []
    for r in results:
        try:
            v = float(r["value"][1])
            if pd.notna(v) and v != float("inf"):
                values.append(v)
        except Exception:
            continue

    return sum(values) / len(values) if values else 0.0


def collect_metrics() -> dict:
    return {
        "rps": query_prometheus(QUERIES["rps"]),
        "latency_p95": query_prometheus(QUERIES["latency_p95"]),
        "memory": query_prometheus(QUERIES["memory"]),
    }

# ========================
# KUBERNETES AUTO-SCALING
# ========================

def scale_kubernetes_deployment(replicas: int):
    print(f"📈 Scaling {DEPLOYMENT_NAME} to {replicas} replicas")

    try:
        config.load_incluster_config()
        apps_v1 = client.AppsV1Api()

        body = {
            "spec": {
                "replicas": replicas
            }
        }

        apps_v1.patch_namespaced_deployment_scale(
            name=DEPLOYMENT_NAME,
            namespace=NAMESPACE,
            body=body
        )

        print("✅ Scaling request sent to Kubernetes API")

    except Exception as e:
        print("❌ Failed to scale deployment:", e)

# ========================
# SLACK ALERTING
# ========================

def send_slack_alert(message: str):
    webhook = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook:
        print("⚠️ Slack webhook not configured")
        return

    payload = {
        "text": message
    }

    try:
        response = requests.post(webhook, json=payload, timeout=5)
        response.raise_for_status()
        print("🔔 Slack alert sent")
    except Exception as e:
        print("❌ Slack alert failed:", e)

# ========================
# MAIN AIOPS CONTROLLER
# ========================

def main():
    print("\n📊 Collecting baseline metrics...\n")

    baseline_data = []

    for _ in range(BASELINE_SAMPLES):
        metrics = collect_metrics()

        # Skip cold-start / idle samples
        if metrics["rps"] == 0.0 and metrics["latency_p95"] == 0.0:
            print("⏭ Skipping cold-start sample:", metrics)
        else:
            baseline_data.append(metrics)
            print("📈 Baseline:", metrics)

        time.sleep(BASELINE_INTERVAL)

    while len(baseline_data) < 10:
        print("⏳ Waiting for sufficient baseline traffic...")
        time.sleep(BASELINE_INTERVAL)
        metrics = collect_metrics()
        if metrics["rps"] > 0:
            baseline_data.append(metrics)
            print("📈 Baseline:", metrics)

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

        # No traffic → ignore
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

                scale_kubernetes_deployment(SCALE_UP_REPLICAS)

                send_slack_alert(
                    f"🚨 *AegisOps Incident Detected*\n"
                    f"Service: {DEPLOYMENT_NAME}\n"
                    f"Namespace: {NAMESPACE}\n"
                    f"Action: Auto-scaled to {SCALE_UP_REPLICAS} replicas\n"
                    f"Metrics: {metrics}\n"
                    f"Time: {datetime.utcnow().isoformat()} UTC"
                )

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

        # Normal behavior
        else:
            print("✅ Normal", metrics)

        time.sleep(MONITOR_INTERVAL)

# ========================
# ENTRYPOINT
# ========================

if __name__ == "__main__":
    main()