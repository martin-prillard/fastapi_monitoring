# FastAPI ML API with Monitoring

A complete example of serving a machine learning model with FastAPI, monitored using Prometheus and Grafana.

## Overview

This project demonstrates how to:
- Serve a machine learning model (Iris classifier) using FastAPI
- Monitor API performance and metrics with Prometheus
- Visualize metrics with Grafana dashboards
- Set up a complete monitoring stack using Docker Compose

## Architecture

The project consists of three main services:

1. **FastAPI Application** - Serves the ML model and exposes metrics
2. **Prometheus** - Collects and stores time-series metrics
3. **Grafana** - Visualizes metrics through dashboards

```
┌──────────┐     ┌─────────────┐     ┌─────────┐
│  FastAPI │────▶│ Prometheus  │────▶│ Grafana │
│  :8000   │     │   :9090     │     │  :3000  │
└──────────┘     └─────────────┘     └─────────┘
     │
     │ /metrics
     │
     ▼
```

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local development)

### Running the Stack

1. Clone this repository
2. Start all services:
```bash
docker compose up --build
```

This will:
- Build the FastAPI application with the trained model
- Start Prometheus to collect metrics
- Start Grafana with pre-configured dashboards

3. Access the services:
   - **FastAPI Swagger UI**: http://localhost:8000/docs
   - **Prometheus UI**: http://localhost:9090
   - **Grafana**: http://localhost:3000 (admin/admin)
   - **Locust Web UI**: http://localhost:8089

## Understanding Prometheus

### What is Prometheus?

Prometheus is an open-source monitoring and alerting toolkit. It collects metrics from your applications and stores them as time-series data.

### How It Works Here

1. **Metrics Collection**: FastAPI exposes metrics at `/metrics` endpoint using the `prometheus-client` library
2. **Scraping**: Prometheus periodically scrapes (polls) the `/metrics` endpoint every 5 seconds (configured in `prometheus.yml`)
3. **Storage**: Prometheus stores the metrics in its time-series database
4. **Querying**: You can query metrics using PromQL (Prometheus Query Language)

### Key Metrics Exposed

- `api_requests_total` - Counter of total API requests
- `api_request_latency_seconds` - Histogram of request latencies

### Prometheus Configuration

The `prometheus.yml` file configures:
- **Scrape interval**: How often to collect metrics (5 seconds)
- **Targets**: Which services to monitor (FastAPI at `fastapi:8000`)
- **Metrics path**: The endpoint to scrape (`/metrics`)

### Using Prometheus

1. **View Targets**: Go to Status → Targets to see if FastAPI is being scraped successfully
2. **Query Metrics**: Use the expression bar to write PromQL queries:
   - `api_requests_total` - Total requests
   - `rate(api_requests_total[1m])` - Requests per second
   - `histogram_quantile(0.95, rate(api_request_latency_seconds_bucket[1m]))` - 95th percentile latency
3. **View Configuration**: Status → Configuration shows the loaded config

### Common PromQL Queries

```promql
# Total requests
api_requests_total

# Request rate (requests per second)
rate(api_requests_total[1m])

# Mean latency
rate(api_request_latency_seconds_sum[1m]) / rate(api_request_latency_seconds_count[1m])

# 95th percentile latency
histogram_quantile(0.95, rate(api_request_latency_seconds_bucket[1m]))

# 99th percentile latency
histogram_quantile(0.99, rate(api_request_latency_seconds_bucket[1m]))
```

## Understanding Grafana

### What is Grafana?

Grafana is an open-source analytics and visualization platform. It connects to data sources (like Prometheus) and creates beautiful dashboards.

### How It Works Here

1. **Data Source**: Grafana is pre-configured to connect to Prometheus (via provisioning)
2. **Dashboards**: Pre-built dashboards are automatically loaded from `grafana/provisioning/dashboards/`
3. **Visualization**: Dashboards display metrics as graphs, stats, gauges, etc.
4. **Real-time Updates**: Dashboards refresh automatically to show current metrics

### Available Dashboards

The project includes four pre-configured dashboards:

1. **FastAPI Monitoring - Overview**
   - Total requests and request rate
   - Latency percentiles (p50, p95, p99)
   - Mean and median latency stats

2. **FastAPI - Latency Analysis**
   - Detailed latency distribution
   - Multiple percentile views
   - Latency heatmap
   - Comparison charts

3. **FastAPI - Request Analysis**
   - Request rate over time
   - Total requests counter
   - Request rate gauges
   - Multiple time window comparisons

4. **FastAPI - Load Testing Dashboard**
   - Real-time metrics during load tests
   - Request rate and latency correlation
   - Latency distribution heatmap
   - Performance indicators under load

### Grafana Features

- **Auto-provisioning**: Dashboards and datasources are automatically configured
- **Interactive queries**: Click on panels to explore data
- **Time range selection**: View metrics over different time periods
- **Alerting**: Set up alerts based on metric thresholds (see Questions & Answers)

### Accessing Dashboards

1. Log in to Grafana (http://localhost:3000) with admin/admin
2. Go to **Dashboards** in the left menu
3. Select a dashboard from the list
4. Dashboards auto-refresh every 10 seconds

## Load Testing with Locust

### What is Locust?

Locust is an open-source load testing tool that allows you to simulate user behavior and test how your API performs under different load conditions. It provides a web-based UI to start tests and monitor results in real-time.

### Running Load Tests

The project includes a pre-configured Locust setup that tests the FastAPI endpoints:

1. **Start all services** (if not already running):
```bash
docker compose up --build
```

2. **Access Locust Web UI**: Open http://localhost:8089 in your browser

3. **Configure and start a test**:
   - **Number of users**: Number of concurrent users to simulate (e.g., 10, 50, 100)
   - **Spawn rate**: How many users to add per second (e.g., 2 users/second)
   - Click **"Start swarming"** to begin the test

4. **Monitor the test**:
   - **Statistics tab**: See request statistics, response times, and failure rates
   - **Charts tab**: View real-time charts of requests per second and response times
   - **Failures tab**: See any failed requests
   - **Exceptions tab**: View any exceptions that occurred

5. **Stop the test**: Click **"Stop"** when you want to end the test

### Visualizing Load Test Results in Grafana

While running a load test, you can monitor the impact on your API in real-time using Grafana:

1. **Open Grafana**: http://localhost:3000 (admin/admin)

2. **Navigate to the Load Testing Dashboard**:
   - Go to **Dashboards** in the left menu
   - Select **"FastAPI - Load Testing Dashboard"**

3. **What to observe during load tests**:
   - **Request Rate**: Watch how the request rate increases as you add more users
   - **Latency Percentiles**: See how latency (p50, p95, p99) changes under load
   - **Latency vs Request Rate**: Observe the correlation between load and response time
   - **Heatmap**: Visualize the distribution of latencies over time

### Load Test Scenarios

The included `locustfile.py` tests three endpoints with different weights:

- **`/predict`** (weight: 3) - Main prediction endpoint, tested most frequently
- **`/`** (weight: 1) - Health check endpoint
- **`/metrics`** (weight: 1) - Metrics endpoint

Users wait 1-3 seconds between requests to simulate realistic behavior.

### Example Load Test Workflow

1. **Baseline test**: Start with 5 users, spawn rate 1 user/sec
   - Observe baseline performance in Grafana
   - Note the request rate and latency

2. **Gradual increase**: Increase to 20 users, spawn rate 2 users/sec
   - Watch how metrics change in Grafana
   - Check if latency increases proportionally

3. **Stress test**: Increase to 50-100 users
   - Monitor for performance degradation
   - Identify breaking points or bottlenecks

4. **Recovery test**: Stop the test and observe how metrics return to baseline

### Tips for Load Testing

- **Start small**: Begin with a few users and gradually increase
- **Monitor Grafana**: Keep the Load Testing Dashboard open to see real-time impact
- **Check Prometheus**: Use Prometheus queries to dive deeper into specific metrics
- **Test different scenarios**: Try different user counts and spawn rates
- **Observe recovery**: After stopping a test, watch how the system recovers

### Customizing Load Tests

To modify the load test behavior, edit `locustfile.py`:

- **Change wait time**: Modify `wait_time = between(1, 3)` to adjust delays
- **Add new tasks**: Add more `@task` decorated methods to test other endpoints
- **Adjust task weights**: Change the weight parameter in `@task()` to change frequency
- **Add test data**: Customize the data sent in requests

## Project Structure

```
.
├── main.py                 # FastAPI application with metrics
├── train_model.py          # Trains and saves the ML model
├── locustfile.py           # Locust load testing configuration
├── pyproject.toml          # Python dependencies (replaces requirements.txt)
├── Dockerfile              # Builds the FastAPI container
├── docker-compose.yml      # Orchestrates all services
├── prometheus.yml          # Prometheus configuration
├── grafana/
│   └── provisioning/
│       ├── datasources/    # Auto-configured Prometheus datasource
│       └── dashboards/     # Pre-built Grafana dashboards
├── README.md               # This file
└── QUESTIONS_AND_ANSWERS.md # Tutorial questions and answers
```

## API Endpoints

### `GET /`
Health check endpoint. Returns a status message.

### `POST /predict`
Makes a prediction using the trained Iris classifier.

**Request body:**
```json
{
  "sepal_length": 5.1,
  "sepal_width": 3.5,
  "petal_length": 1.4,
  "petal_width": 0.2
}
```

**Response:**
```json
{
  "prediction": 0
}
```

### `GET /metrics`
Exposes Prometheus metrics in the format Prometheus expects. This endpoint is scraped by Prometheus.

## Monitoring Flow

1. **Request arrives** at FastAPI `/predict` endpoint
2. **Metrics recorded**: 
   - Request counter incremented
   - Latency timer started
3. **Prediction made**: Model processes the input
4. **Metrics finalized**: Latency recorded
5. **Response sent** to client
6. **Prometheus scrapes** `/metrics` endpoint (every 5 seconds)
7. **Grafana queries** Prometheus to display metrics in dashboards

## Development

### Local Development (without Docker)

1. Install dependencies:
```bash
pip install -e .
```

2. Train the model:
```bash
python train_model.py
```

3. Run the API:
```bash
uvicorn main:app --reload
```

### Modifying Dashboards

1. Edit JSON files in `grafana/provisioning/dashboards/`
2. Restart Grafana: `docker compose restart grafana`
3. Changes will be reflected in Grafana UI

### Adding New Metrics

1. Add metric to `main.py` using `prometheus_client`:
```python
from prometheus_client import Counter, Histogram, Gauge

ERROR_COUNT = Counter("api_errors_total", "Total API errors")
```

2. Use the metric in your code
3. Restart the FastAPI service
4. The metric will automatically appear in Prometheus
5. Add it to Grafana dashboards as needed

## Troubleshooting

### Prometheus can't scrape FastAPI

- Check that both services are on the same Docker network
- Verify FastAPI is running: `curl http://localhost:8000/`
- Check Prometheus targets: http://localhost:9090/targets
- Ensure the service name in `prometheus.yml` matches docker-compose service name

### Grafana shows "No data"

- Verify Prometheus datasource is configured (should be auto-configured)
- Check datasource connection: Configuration → Data Sources → Prometheus → Test
- Ensure Prometheus is collecting data: http://localhost:9090
- Check that metrics exist: Query `api_requests_total` in Prometheus

### Dashboards not appearing

- Check Grafana logs: `docker compose logs grafana`
- Verify dashboard files are in `grafana/provisioning/dashboards/`
- Ensure dashboard JSON is valid
- Restart Grafana: `docker compose restart grafana`

## Questions and Tutorial

For detailed questions and answers about the project, architecture, and monitoring concepts, see [QUESTIONS_AND_ANSWERS.md](QUESTIONS_AND_ANSWERS.md).

## License

This is an educational project for learning API monitoring and observability.
