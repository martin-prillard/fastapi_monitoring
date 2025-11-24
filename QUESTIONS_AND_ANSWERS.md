# Questions and Answers

This document contains all the questions from the tutorial along with detailed answers.

## First part : File analysis

### Question 1:
**What services are being built using this docker compose? Are they all built the same way? How are they connected?**

**Answer:**
The docker-compose file builds three services:
1. **FastAPI** - Built from a Dockerfile in the current directory (custom build)
2. **Prometheus** - Uses the official `prom/prometheus:latest` image (pre-built)
3. **Grafana** - Uses the official `grafana/grafana:latest` image (pre-built)

They are not all built the same way:
- FastAPI is built from a Dockerfile, which installs Python dependencies and trains the ML model
- Prometheus and Grafana use pre-built Docker images

They are connected through a Docker bridge network named `monitoring`. All services can communicate with each other using their service names (fastapi, prometheus, grafana) as hostnames.

### Question 2:
**Can you identify a potential security problem if you were to put that in production "as is"?**

**Answer:**
Yes, several security issues:
1. **Default credentials**: Grafana uses hardcoded admin/admin credentials that are visible in the docker-compose file
2. **No authentication**: The FastAPI endpoints have no authentication or rate limiting
3. **Exposed ports**: All services expose ports directly to the host without any reverse proxy or firewall
4. **No HTTPS/TLS**: All communication is over HTTP, not encrypted
5. **Model file**: The model is included in the Docker image, which could be a security concern if the model contains sensitive information

### Question 3:
**What happens to the stored metrics if one of the monitoring services fails?**

**Answer:**
- **If Prometheus fails**: Metrics collection stops, and historical data stored in Prometheus would be lost (unless Prometheus has persistent storage configured, which it doesn't in the current setup). The FastAPI app continues to serve metrics at `/metrics`, but they won't be scraped.
- **If Grafana fails**: Visualization stops, but Prometheus continues collecting metrics. Once Grafana restarts, it can reconnect to Prometheus and display the data that was collected during Grafana's downtime.
- **If FastAPI fails**: No new metrics are generated, but Prometheus retains historical metrics until its retention period expires.

**Note**: The current setup doesn't use persistent volumes, so all data is lost when containers are removed.

### Question 4:
**Let's focus on the FastAPI. How many endpoints can you identify? What are they used for? What is the difference between GET and POST? How can you verify that the API is indeed running?**

**Answer:**
The FastAPI application has 3 endpoints:
1. `GET /` - Health check endpoint that returns a status message
2. `POST /predict` - Accepts iris flower measurements and returns a prediction
3. `GET /metrics` - Exposes Prometheus metrics in the format Prometheus expects

**GET vs POST:**
- **GET**: Used for retrieving data, should be idempotent (same request = same result), parameters in URL
- **POST**: Used for submitting data, can have side effects, data in request body

**Verification:**
- Visit `http://localhost:8000/docs` for the Swagger UI
- Visit `http://localhost:8000/` to see the health check message
- Visit `http://localhost:8000/metrics` to see Prometheus metrics
- Use curl: `curl http://localhost:8000/`

### Question 5:
**Why wouldn't it be a good idea to add the possibility to train using the API?**

**Answer:**
Several reasons:
1. **Resource intensive**: Training is CPU/memory intensive and could crash the API server
2. **Blocking**: Training would block request handling, making the API unresponsive
3. **Security**: Allowing arbitrary training could be exploited (model poisoning, resource exhaustion)
4. **State management**: Training changes the model state, affecting all future predictions
5. **No versioning**: Hard to track which model version is being used
6. **Data privacy**: Training data might contain sensitive information
7. **Best practice**: Training and serving should be separate processes (MLOps principle)

### Question 6:
**Let's focus on the prometheus.yml file. What is it about?**

**Answer:**
The `prometheus.yml` file is Prometheus's configuration file. It defines:
- **Global settings**: `scrape_interval: 5s` - how often Prometheus scrapes metrics (every 5 seconds)
- **Scrape configs**: Defines what to monitor
  - `job_name: "fastapi"` - Name for this monitoring job
  - `metrics_path: /metrics` - The endpoint to scrape
  - `targets: ["fastapi:8000"]` - The service name and port to scrape from

This tells Prometheus to collect metrics from the FastAPI service's `/metrics` endpoint every 5 seconds.

### Question 7:
**Let's focus on the fastapi_dashboard.json file. What is it about?**

**Answer:**
The `fastapi_dashboard.json` file is a Grafana dashboard configuration. It defines:
- **Dashboard metadata**: Title, tags, version, schema version
- **Panels**: Visualizations (graphs, stats, etc.)
  - Each panel has queries (PromQL expressions) to fetch data from Prometheus
  - Layout information (grid position, size)
  - Visualization type (graph, stat, etc.)

This dashboard automatically loads into Grafana when the container starts, providing pre-configured visualizations of the FastAPI metrics.

## Second part : Hands on

### Question 1:
**Launch a few requests using the FastAPI swagger to make some basic predictions. What is the model used behind those predictions? Would we get an error if we performed inference for a data point largely out of distribution?**

**Answer:**
- The model is a **RandomForestClassifier** trained on the Iris dataset (see `train_model.py`)
- **Out of distribution**: The current implementation would NOT return an error for OOD data. The model would still make a prediction (likely incorrect), but there's no validation. This is a problem because:
  - The model was trained on iris measurements (typically: sepal_length 4-8, sepal_width 2-5, petal_length 1-7, petal_width 0-3)
  - If you send values like sepal_length=100, the model will still predict, but the prediction is meaningless

### Question 2:
**In the POST endpoint of the API, add a way to check if a datapoint is largely out of distribution and if it is the case, return a warning in the response content.**

**Answer:**
This would require implementing OOD detection. Common approaches:
- Statistical bounds checking (min/max values from training data)
- Z-score or Mahalanobis distance
- Isolation Forest or other anomaly detection models
- Confidence threshold checking

The implementation would validate input features against expected ranges and return a warning in the response if values are suspicious.

### Question 3:
**What is a huge limitation in terms of speed & network throughput in the case a user wants several predictions instead of only one?**

**Answer:**
The limitation is that each prediction requires a separate HTTP request. If a user needs 1000 predictions:
- **1000 separate HTTP requests** = high overhead (connection setup, headers, etc.)
- **Network latency** multiplied by number of requests
- **No batching** - can't process multiple predictions efficiently

**Solution**: Add a batch prediction endpoint that accepts multiple inputs in one request and returns multiple predictions.

### Question 4:
**In Prometheus, where can you check the endpoint to which it is linked?**

**Answer:**
In Prometheus UI (`http://localhost:9090`):
1. Go to **Status → Targets** to see all configured scrape targets
2. Go to **Status → Configuration** to see the full `prometheus.yml` configuration
3. The target should show as "UP" if it's successfully scraping from `fastapi:8000/metrics`

### Question 5:
**Once you ensured Prometheus is linked to the FastAPI metrics endpoint, use the FastAPI swagger to generate a handful of new predictions. Type your first request in the expression bar: `api_requests_total`. What info does it give us? How can you check that the information is retained through time, so that you can follow the evolution of the use of your API?**

**Answer:**
- `api_requests_total` shows the **cumulative total number of requests** since the API started
- It's a counter metric that only increases
- To see evolution over time:
  - Use the **Graph** tab (not Table) to see the metric plotted over time
  - The graph will show a step function increasing with each request
  - Use `rate(api_requests_total[1m])` to see requests per second instead of total count

### Question 6:
**In regard to question 3, how is this indicator kind of rigged?**

**Answer:**
The `api_requests_total` counter is "rigged" because:
- It counts **all requests** to the `/predict` endpoint, regardless of whether they're from the same user making multiple requests or different users
- If someone makes 1000 requests in a loop (simulating batch predictions), it inflates the metric
- It doesn't distinguish between:
  - Single user making many requests (testing, batch processing)
  - Many users making few requests (normal usage)
- Better metrics would include: unique users, requests per user, batch size, etc.

### Question 7:
**Let's launch a little more complex command: `histogram_quantile(0.95, rate(api_request_latency_seconds_bucket[1m]))`. What are we aiming to achieve by using this command? What is the reason behind the graph spiking?**

**Answer:**
- This calculates the **95th percentile latency** - meaning 95% of requests are faster than this value
- `histogram_quantile(0.95, ...)` - gets the 95th percentile
- `rate(...[1m])` - calculates the rate over 1 minute window
- `api_request_latency_seconds_bucket` - histogram buckets containing latency distribution

**Graph spiking reasons:**
- **Cold start**: First request after idle period (model loading, Python warmup)
- **System load**: CPU/memory contention
- **Network latency**: If testing from outside Docker network
- **Garbage collection**: Python GC pauses
- **Small sample size**: With few requests, percentiles can be volatile

### Question 8:
**In Grafana, we don't have access yet to the data stored by Prometheus. Check the Connections/ Data Sources panel. We have to connect them using the button "Add new Data Source". Choose Prometheus and modify the Prometheus server URL to be http://prometheus:9090. Congratulations, they are now linked.**

**Answer:**
With the new provisioning setup, the Prometheus datasource is automatically configured. However, if manual setup is needed:
1. Go to **Configuration → Data Sources**
2. Click **Add data source**
3. Select **Prometheus**
4. Set URL to `http://prometheus:9090` (using Docker service name)
5. Click **Save & Test**

The datasource is now linked and Grafana can query Prometheus.

### Question 9:
**We will now have to get our dashboard running. Go to the Dashboards panel, click on the "New" button, and choose "Import" to import the fastapi_dashboard.json file. You should now be able to see the dashboards. Modify the filters and edit them so that they look prettier and more readable. You can also design a python script that requests the API randomly and "en masse" to simulate the real usage of your API.**

**Answer:**
With provisioning, dashboards are automatically imported. For manual import:
1. Go to **Dashboards → Import**
2. Upload `fastapi_dashboard.json` or paste its contents
3. Select the Prometheus datasource
4. Click **Import**

**Load testing script example:**
```python
import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor

def make_prediction():
    data = {
        "sepal_length": random.uniform(4, 8),
        "sepal_width": random.uniform(2, 5),
        "petal_length": random.uniform(1, 7),
        "petal_width": random.uniform(0, 3)
    }
    response = requests.post("http://localhost:8000/predict", json=data)
    return response.json()

# Simulate load
with ThreadPoolExecutor(max_workers=10) as executor:
    for _ in range(1000):
        executor.submit(make_prediction)
        time.sleep(0.1)  # 10 requests per second
```

### Question 10:
**Create a new grafana dashboard to provide the median and mean latency of your requests to the API.**

**Answer:**
This is now included in the "FastAPI - Latency Analysis" dashboard:
- **Mean latency**: `rate(api_request_latency_seconds_sum[1m]) / rate(api_request_latency_seconds_count[1m])`
- **Median latency (p50)**: `histogram_quantile(0.50, rate(api_request_latency_seconds_bucket[1m]))`

Both are displayed as stat panels and time series graphs.

### Question 11:
**Consult Grafana documentation to get more familiar with the framework. What could we want to do to react very quickly to a sudden spike in our mean API latency?**

**Answer:**
We should set up **Grafana Alerts**:
1. Create an alert rule that monitors mean latency
2. Set threshold (e.g., mean latency > 0.5s for 1 minute)
3. Configure notification channels (email, Slack, PagerDuty, etc.)
4. Set up alert rules with conditions and evaluation intervals

**Steps:**
- Go to **Alerting → Alert Rules → New Alert Rule**
- Query: `rate(api_request_latency_seconds_sum[1m]) / rate(api_request_latency_seconds_count[1m])`
- Condition: `WHEN last() OF query(A, 1m, now) IS ABOVE 0.5`
- Add notification channel

This enables proactive monitoring and rapid response to performance issues.

### Question 12:
**Overall, what is your conclusion on why adding a monitoring system might be important to ensure everything runs smoothly without having to check every system you deployed manually?**

**Answer:**
**Key benefits:**
1. **Proactive problem detection**: Identify issues before users complain
2. **Performance optimization**: Understand bottlenecks and optimize accordingly
3. **Capacity planning**: Predict when to scale based on trends
4. **Debugging**: Historical data helps diagnose issues
5. **SLA compliance**: Monitor and ensure service level agreements are met
6. **Cost optimization**: Identify inefficient resource usage
7. **Automation**: Alerts reduce need for manual checking
8. **Business insights**: Understand usage patterns and user behavior

**Without monitoring**: You're "flying blind" - issues are discovered by users, debugging is harder, and you can't optimize effectively.

### Question 13:
**What typical metrics do we want to log?**

**Answer:**
**The Four Golden Signals** (Google SRE):
1. **Latency**: Request duration (mean, median, p95, p99)
2. **Traffic**: Request rate, throughput
3. **Errors**: Error rate, error types (4xx, 5xx)
4. **Saturation**: Resource utilization (CPU, memory, disk, network)

**Additional important metrics:**
- **Availability/Uptime**: Service health
- **Request size**: Payload sizes
- **Response size**: Response payload sizes
- **Concurrent requests**: Active connections
- **Queue depth**: If using queues
- **Business metrics**: Predictions made, model confidence, etc.

### Question 14:
**How should we modify our system to add CPU usage tracking to our Grafana dashboards? Do it.**

**Answer:**
To add CPU usage tracking:

1. **Install node_exporter** (system metrics exporter) or use cAdvisor (container metrics)
2. **Add to docker-compose.yml**:
```yaml
cadvisor:
  image: gcr.io/cadvisor/cadvisor:latest
  ports:
    - "8080:8080"
  volumes:
    - /:/rootfs:ro
    - /var/run:/var/run:ro
    - /sys:/sys:ro
    - /var/lib/docker/:/var/lib/docker:ro
  networks:
    - monitoring
```

3. **Update prometheus.yml** to scrape cAdvisor:
```yaml
scrape_configs:
  - job_name: "cadvisor"
    static_configs:
      - targets: ["cadvisor:8080"]
```

4. **Create Grafana dashboard** with CPU queries:
   - `rate(container_cpu_usage_seconds_total{name="fastapi_app"}[1m])`
   - `container_memory_usage_bytes{name="fastapi_app"}`

This provides container-level CPU and memory metrics for the FastAPI service.

