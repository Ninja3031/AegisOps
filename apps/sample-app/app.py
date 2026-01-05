from flask import Flask
import time, random
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP Requests"
)

REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "Request latency"
)

@app.route("/")
@REQUEST_LATENCY.time()
def home():
    REQUEST_COUNT.inc()
    if random.random() > 0.8:
        time.sleep(5)  # intentional latency spike
    return "AegisOps App Running"

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

app.run(host="0.0.0.0", port=5000)