# AegisOps
AIOps system that detects anomalies in Kubernetes workloads and automatically remediates failures using ML + intelligent automation


🚀 AegisOps — AI-Driven Self-Healing Kubernetes Platform

AegisOps is an AI-powered AIOps platform that continuously monitors application performance metrics, detects anomalies using machine learning, and automatically triggers Kubernetes remediation actions such as auto-scaling — with observability, alerting, and CI/CD built in.

This project demonstrates modern DevOps + AIOps practices aligned with 2026 recruiter expectations.

⸻

📌 Why This Project Matters (Recruiter Context)

Traditional Kubernetes relies on static thresholds (HPA, alerts).
AegisOps goes further by introducing AI-driven decision making:
	•	Detects non-obvious anomalies using ML (Isolation Forest)
	•	Correlates traffic, latency, and memory
	•	Performs autonomous remediation
	•	Integrates Prometheus, Grafana, Slack, CI/CD
	•	Designed with production-grade architecture principles

This is not a demo script — it is a system.

⸻

🧠 Core Capabilities

✅ AI-Driven Anomaly Detection
	•	Uses Isolation Forest (unsupervised ML)
	•	Learns baseline behavior dynamically
	•	Detects:
	•	Latency spikes
	•	Traffic irregularities
	•	Memory anomalies

✅ Autonomous Kubernetes Remediation
	•	Runs inside the cluster as a pod
	•	Uses Kubernetes API (in-cluster auth)
	•	Automatically:
	•	Scales deployments
	•	Applies cooldowns to avoid loops

✅ Observability-First Design
	•	Prometheus for metrics
	•	Grafana dashboards for visualization
	•	Real-time metrics ingestion

✅ Incident Alerting
	•	Slack alerts for:
	•	Anomaly detection
	•	Auto-healing actions
	•	Configured via Kubernetes Secrets

✅ CI/CD Automation
	•	GitHub Actions pipeline:
	•	Python validation
	•	Docker image build
	•	Secure push to Docker Hub
	•	Kubernetes deployment handled separately (local cluster design)


    🏗️ High-Level Architecture

+--------------------+
|  Client Traffic    |
+--------------------+
          |
          v
+--------------------+
| Application Pods   |
| (aegisops-app)     |
+--------------------+
          |
          v
+--------------------+        +-------------------+
| Prometheus         | <----> | Grafana           |
| (Metrics Store)    |        | (Dashboards)      |
+--------------------+        +-------------------+
          |
          v
+------------------------------------------------+
| AegisOps AI Engine (Kubernetes Pod)            |
|                                                |
| - Metric collection via PromQL                 |
| - ML anomaly detection                         |
| - Kubernetes auto-scaling                      |
| - Slack alerting                               |
+------------------------------------------------+


Technology Stack

Layer                 Technology
Containerization      Docker
Orchestration         Kubernetes (Kind / Local)
Monitoring            Prometheus
Visualization         Grafana
AI / ML               Python, Scikit-Learn (Isolation Forest)
CI/CD                 GitHub Actions
Alerting              Slack Webhooks
Language              Python 3.1


Repository Structure

AegisOps/
├── ai-engine/
│   ├── anomaly_detector.py     # Core AIOps logic
│   ├── Dockerfile              # AI engine container
│   └── requirements.txt
│
├── kubernetes/
│   ├── app-deployment.yaml     # Sample application
│   ├── ai-engine-deployment.yaml
│   ├── rbac.yaml               # Least-privilege RBAC
│   └── loadgen.yaml            # Traffic generator
│
├── .github/
│   └── workflows/
│       └── aegisops-ci-cd.yml  # CI/CD pipeline
│
└── README.md


⚙️ How AegisOps Works (Step-by-Step)

1️⃣ Baseline Learning
	•	AI engine queries Prometheus
	•	Collects baseline metrics:
	•	Requests per second (RPS)
	•	P95 latency
	•	Memory usage
	•	Filters cold-start / idle samples
	•	Trains Isolation Forest model

2️⃣ Continuous Monitoring
	•	Periodic PromQL queries
	•	Real-time inference against baseline

3️⃣ Anomaly Detection
	•	ML model flags abnormal behavior
	•	Cooldown logic prevents flapping

4️⃣ Autonomous Remediation
	•	Kubernetes API invoked from inside cluster
	•	Deployment auto-scaled
	•	Slack notification sent


📊 Metrics Used (PromQL)

rate(http_requests_total[1m])

histogram_quantile(
  0.95,
  rate(http_request_latency_seconds_bucket[1m])
)

process_resident_memory_bytes


🔐 Security & RBAC
	•	Uses dedicated ServiceAccount
	•	Minimal permissions:
	•	get, list, patch on deployments/scale
	•	Slack webhook stored in Kubernetes Secret
	•	No hard-coded credentials

⸻

🔁 CI/CD Pipeline Details

CI Stage
	•	Python syntax validation
	•	Import checks
	•	Dependency verification

CD Stage
	•	Docker image build
	•	Secure push to Docker Hub using access tokens
	•	Kubernetes deployment intentionally skipped (local cluster)

⚠️ Why deploy is skipped in CI/CD

This project uses a local Kind cluster, which is not reachable from GitHub Actions runners.
In production, the same pipeline would target EKS/GKE/AKS.


▶️ How to Run Locally

1️⃣ Start cluster

kind create cluster --name aegisops

2️⃣ Deploy monitoring stack

helm install monitoring prometheus-community/kube-prometheus-stack -n aegisops --create-namespace

3️⃣ Deploy app and AI engine

kubectl apply -f kubernetes/

4️⃣ Generate traffic

kubectl apply -f kubernetes/loadgen.yaml

5️⃣ View logs

kubectl logs -l app=aegisops-ai-engine -n aegisops -f

🧠 Design Decisions (Interview-Ready)
	•	AI instead of static thresholds → reduces false positives
	•	In-cluster AI engine → true autonomy
	•	Cooldown logic → avoids scaling loops
	•	Observability-first → metrics before automation
	•	Security-first → RBAC + secrets
	•	CI/CD decoupled from runtime infra → realistic DevOps practice

⸻

🚀 Future Enhancements
	•	HPA feedback loop driven by AI
	•	Multi-service anomaly correlation
	•	Canary-based remediation
	•	Auto-rollback on failed scale-up
	•	LLM-based root cause analysis
	•	Cloud-native deployment (EKS/GKE)


This project demonstrates real-world AIOps engineering, not toy scripts.
It reflects how modern DevOps teams design resilient, autonomous systems using Kubernetes, ML, and observability.

____



