"""
Main FastAPI application
Python layer - aggregates and formats data from Java layer to Arrow/JSON

Hybrid Architecture:
- Control Plane (REST): Authentication, session management, flight preparation
- Data Plane (gRPC): High-throughput Arrow Flight streaming
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from typing import Optional
import logging
import threading

from app.services.java_client import JavaLayerClient
from app.services.aggregator import DataAggregator
from app.services.arrow_formatter import ArrowFormatter
from app.services.json_formatter import JSONFormatter
from app.services.flight_server import ExcelFlightServer
from app.services.flight_rest_bridge import router as flight_router, set_flight_server
from app.models.schemas import ParseResponse, ExcelProcessRequest
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Excel Parser - Python Aggregation Layer",
    description="Hybrid architecture: REST (control) + Arrow Flight (data streaming)",
    version="2.0.0"
)

# Initialize services
java_client = JavaLayerClient(settings.java_layer_url)
aggregator = DataAggregator()
arrow_formatter = ArrowFormatter()
json_formatter = JSONFormatter()

# Initialize Arrow Flight server (data plane)
flight_location = f"grpc://{settings.flight_host}:{settings.flight_port}"
flight_server = ExcelFlightServer(flight_location)
set_flight_server(flight_server)

# Include Flight REST bridge routes
app.include_router(flight_router)


@app.get("/")
async def root():
    return {
        "service": "Excel Parser - Python Layer",
        "version": "2.0.0",
        "architecture": "Hybrid (REST + Arrow Flight)",
        "status": "running",
        "endpoints": {
            "control_plane": {
                "rest_api": f"http://localhost:{settings.api_port}",
                "health": "/health",
                "legacy_upload": "/api/v1/process/excel",
                "flight_prepare": "/api/v1/flight/prepare",
                "flight_list": "/api/v1/flight/list"
            },
            "data_plane": {
                "grpc_streaming": f"grpc://localhost:{settings.flight_port}",
                "protocol": "Arrow Flight",
                "example": "/api/v1/flight/example"
            }
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    java_health = await java_client.health_check()
    return {
        "python_layer": "healthy",
        "java_layer": java_health
    }


@app.post("/api/v1/process/excel")
async def process_excel(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    output_format: str = Query("json", regex="^(json|arrow)$"),
    aggregate: bool = Query(True)
):
    """
    Process Excel file end-to-end:
    1. Send to Java layer for POI parsing
    2. Aggregate results
    3. Format as Arrow or JSON
    """
    logger.info(f"Processing Excel file: {file.filename}")

    try:
        # Step 1: Parse with Java layer
        parse_response = await java_client.parse_excel(
            file=file,
            sheet_name=sheet_name,
            region=region
        )

        # Step 2: Aggregate data
        if aggregate:
            aggregated_data = aggregator.aggregate(parse_response)
        else:
            aggregated_data = parse_response

        # Step 3: Format output
        if output_format == "arrow":
            arrow_bytes = arrow_formatter.format(aggregated_data)
            return Response(
                content=arrow_bytes,
                media_type="application/vnd.apache.arrow.stream"
            )
        else:
            json_data = json_formatter.format(aggregated_data)
            return JSONResponse(content=json_data)

    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/process/excel-from-path")
async def process_excel_from_path(request: ExcelProcessRequest):
    """
    Process Excel file from path:
    1. Java layer parses from file path
    2. Aggregate and format results
    """
    logger.info(f"Processing Excel from path: {request.file_path}")

    try:
        # Step 1: Parse with Java layer
        parse_response = await java_client.parse_excel_from_path(
            file_path=request.file_path,
            sheet_name=request.sheet_name,
            region=request.region
        )

        # Step 2: Aggregate data
        if request.aggregate:
            aggregated_data = aggregator.aggregate(parse_response)
        else:
            aggregated_data = parse_response

        # Step 3: Format output
        if request.output_format == "arrow":
            arrow_bytes = arrow_formatter.format(aggregated_data)
            return Response(
                content=arrow_bytes,
                media_type="application/vnd.apache.arrow.stream"
            )
        else:
            json_data = json_formatter.format(aggregated_data)
            return JSONResponse(content=json_data)

    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def start_flight_server_background():
    """Start Arrow Flight server in background thread"""
    logger.info(f"Starting Arrow Flight server on {flight_location}")
    flight_server.serve()


if __name__ == "__main__":
    import uvicorn

    # Start Flight server in background thread (data plane)
    flight_thread = threading.Thread(target=start_flight_server_background, daemon=True)
    flight_thread.start()
    logger.info("Arrow Flight server thread started")

    # Start FastAPI server (control plane)
    logger.info(f"Starting REST API on {settings.api_host}:{settings.api_port}")
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
