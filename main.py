"""
FastAPI ML API for Iris Flower Classification.

This module provides a RESTful API for predicting Iris flower species
using a pre-trained machine learning model. The API includes Prometheus
metrics for monitoring request counts and latency.

Endpoints:
    GET /: Health check endpoint
    POST /predict: Predict Iris flower species from input features
    GET /metrics: Prometheus metrics endpoint
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi.responses import Response
import joblib
import time
from typing import Dict, Any

app = FastAPI(title="Iris ML API", version="1.0")

# Load the pre-trained machine learning model
model = joblib.load("model.joblib")

# Prometheus metrics
REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total number of API requests",
)
REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds",
    "Request latency in seconds",
)


class IrisInput(BaseModel):
    """
    Input model for Iris flower classification.

    This model represents the four features required for predicting
    the Iris flower species: sepal and petal dimensions.

    Attributes:
        sepal_length: Length of the sepal in centimeters.
        sepal_width: Width of the sepal in centimeters.
        petal_length: Length of the petal in centimeters.
        petal_width: Width of the petal in centimeters.

    Example:
        {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        }
    """

    sepal_length: float = Field(
        ...,
        description="Sepal length in centimeters",
        gt=0,
    )
    sepal_width: float = Field(
        ...,
        description="Sepal width in centimeters",
        gt=0,
    )
    petal_length: float = Field(
        ...,
        description="Petal length in centimeters",
        gt=0,
    )
    petal_width: float = Field(
        ...,
        description="Petal width in centimeters",
        gt=0,
    )


@app.get("/", status_code=status.HTTP_200_OK)
def root() -> Dict[str, str]:
    """
    Root endpoint for health check.

    Returns a simple message indicating that the API is running.
    This endpoint can be used to verify that the service is up
    and responding to requests.

    Returns:
        Dict[str, str]: A dictionary containing a status message.

    Example:
        >>> response = {"message": "FastAPI ML API is running"}
    """
    return {"message": "FastAPI ML API is running"}


@app.post("/predict", status_code=status.HTTP_200_OK)
def predict(data: IrisInput) -> Dict[str, int]:
    """
    Predict Iris flower species from input features.

    This endpoint accepts the four Iris flower measurements (sepal and
    petal dimensions) and returns the predicted species class. The
    prediction is performed using a pre-trained machine learning model.

    The endpoint tracks metrics:
        - Total request count (incremented for each request)
        - Request latency (measured in seconds)

    Args:
        data: IrisInput model containing the four flower measurements.

    Returns:
        Dict[str, int]: A dictionary containing the predicted class.
            The prediction is an integer representing the species:
            - 0: Setosa
            - 1: Versicolor
            - 2: Virginica

    Raises:
        HTTPException: If the prediction fails or input validation fails.
            Status code 400 with error details.

    Example:
        >>> input_data = IrisInput(
        ...     sepal_length=5.1,
        ...     sepal_width=3.5,
        ...     petal_length=1.4,
        ...     petal_width=0.2
        ... )
        >>> response = predict(input_data)
        >>> # Returns: {"prediction": 0}
    """
    REQUEST_COUNT.inc()
    start = time.time()
    try:
        features = [[
            data.sepal_length,
            data.sepal_width,
            data.petal_length,
            data.petal_width,
        ]]
        pred = int(model.predict(features)[0])
        return {"prediction": pred}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    finally:
        REQUEST_LATENCY.observe(time.time() - start)


@app.get("/metrics")
def metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus format that can be scraped by
    a Prometheus server. This endpoint exposes various metrics
    including request counts and latency histograms.

    Returns:
        Response: HTTP response containing Prometheus-formatted metrics
            with content type 'text/plain; version=0.0.4; charset=utf-8'.

    Example:
        The response will contain metrics like:
        # HELP api_requests_total Total number of API requests
        # TYPE api_requests_total counter
        api_requests_total 42.0
        # HELP api_request_latency_seconds Request latency in seconds
        # TYPE api_request_latency_seconds histogram
        ...
    """
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
