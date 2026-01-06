#Here we have used flask for keeping the application light weight,fast startup and minimal overhead and 
#perfect for microservices inside kubernetes

from flask import Flask

#--Time--
#imported time and random to introduce artificial latency (Artificial latency is an intentionally introduced delay to simulate real-world performance issues, 
#allowing us to test monitoring, alerting, and system resilience)
#--Random--
#The random module is used to simulate non-deterministic behavior seen in real systems, where only a subset of requests experience latency due to resource contention or external dependencies.

import time, random

#These have been imported from the python prometheus client library used pip install 
#Prometheus is used for Collecting metrics, Monitor performance, Trigger Alerts, Visuslize data(via Grafana)
#here my flask app is acting as a metrics exporter
#--Counter--
#Counter is used for counting the number of http requests handled by the app(meaning the client that access my flask app)
#It is used for measuring Traffic Volume, Detect Sudden spikes, Identify abnormal Request Rates.
#--Histogram--
#Measures how long requests take, groups latency into buckets, Helps calculate p50,p95,p99 latency 
#Histogram Helps detect slow requets , tail latency(slowest request in my system) and performance degradation
#--generate_latest
#generate_latest() collects all metrics created in your app and converts them into a text format that Prometheus understands.

from prometheus_client import Counter, Histogram, generate_latest

#--Content_Type_Latest
#CONTENT_TYPE_LATEST tells Prometheus “this response contains metrics in the correct format.”
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
#this request latency starts a timer before the request and stops it after the response this way it calculates the latency
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


#✅ /metrics endpoint – why it exists
# /metrics endpoint is used by Prometheus to scrape application metrics.
# It exposes internal performance and health data in a Prometheus-compatible format.
# This endpoint is meant only for monitoring systems, not end users.


#✅ Prometheus scrape cycle
# Prometheus follows a pull-based model:
# It periodically sends HTTP requests to /metrics,
# collects the latest metrics, and stores them as time-series data
# for monitoring, visualization, and alerting.

#✅ Why /metrics must be fast (slow metrics impact)
# IMPORTANT: /metrics must remain lightweight and fast.
# If this endpoint becomes slow or times out,
# Prometheus fails the scrape and may mark the service as DOWN,
# leading to gaps in monitoring and missed alerts.