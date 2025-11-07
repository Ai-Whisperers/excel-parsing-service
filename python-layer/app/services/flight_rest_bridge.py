"""
Arrow Flight REST Bridge
Control plane: REST endpoints for Flight operations
Data plane: Flight streaming for actual data transfer
"""

import logging
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Optional
import pyarrow.flight as flight
import json

from app.services.flight_server import ExcelFlightServer, process_excel_to_flight
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/flight", tags=["Arrow Flight"])

# Global Flight server reference (will be injected at startup)
_flight_server: Optional[ExcelFlightServer] = None


def set_flight_server(server: ExcelFlightServer):
    """Set the global Flight server instance"""
    global _flight_server
    _flight_server = server


@router.post("/prepare")
async def prepare_flight(
    file_path: str = Query(..., description="Path to Excel file"),
    sheet_name: Optional[str] = Query(None),
    region: Optional[str] = Query(None)
):
    """
    Control Plane: Prepare Excel file for streaming

    Returns flight_id and schema for client to connect via gRPC
    """
    if not _flight_server:
        raise HTTPException(status_code=503, detail="Flight server not initialized")

    try:
        # Process Excel and create flight
        flight_id = await process_excel_to_flight(
            _flight_server,
            file_path=file_path,
            sheet_name=sheet_name,
            region=region
        )

        # Get flight info
        flight_data = _flight_server.flights[flight_id]

        # Convert schema to JSON for REST response
        schema_json = {
            'names': flight_data['schema'].names,
            'types': [str(t) for t in flight_data['schema'].types],
            'metadata': dict(flight_data['schema'].metadata) if flight_data['schema'].metadata else {}
        }

        return {
            "flight_id": flight_id,
            "schema": schema_json,
            "total_records": flight_data['total_records'],
            "grpc_endpoint": f"grpc://localhost:{settings.flight_port}",
            "ticket": f"excel:{flight_id}:{{}}",
            "instructions": {
                "1_connect": f"Connect to gRPC endpoint: grpc://localhost:{settings.flight_port}",
                "2_get_data": f"Use DoGet with ticket: excel:{flight_id}:{{}}",
                "3_example": "See /flight/example for client code"
            }
        }

    except Exception as e:
        logger.error(f"Error preparing flight: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_excel_stream(
    file: UploadFile = File(...),
    flight_id: str = Query(..., description="Flight ID to create")
):
    """
    Control Plane: Upload Excel file and prepare for streaming

    Combines file upload + flight preparation in one call
    """
    if not _flight_server:
        raise HTTPException(status_code=503, detail="Flight server not initialized")

    try:
        # Save uploaded file temporarily
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Process and create flight
        try:
            created_flight_id = await process_excel_to_flight(
                _flight_server,
                file_path=tmp_path
            )

            # Get flight info
            flight_data = _flight_server.flights[created_flight_id]

            return {
                "flight_id": created_flight_id,
                "total_records": flight_data['total_records'],
                "grpc_endpoint": f"grpc://localhost:{settings.flight_port}",
                "message": "File uploaded and ready for streaming via gRPC"
            }
        finally:
            # Cleanup temp file
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Error uploading to flight: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_flights():
    """
    Control Plane: List all available flights
    """
    if not _flight_server:
        raise HTTPException(status_code=503, detail="Flight server not initialized")

    flights = []
    for flight_id, flight_data in _flight_server.flights.items():
        flights.append({
            "flight_id": flight_id,
            "total_records": flight_data['total_records'],
            "schema_fields": len(flight_data['schema'].names)
        })

    return {
        "flights": flights,
        "count": len(flights),
        "grpc_endpoint": f"grpc://localhost:{settings.flight_port}"
    }


@router.get("/info/{flight_id}")
async def get_flight_info(flight_id: str):
    """
    Control Plane: Get detailed info about a specific flight
    """
    if not _flight_server:
        raise HTTPException(status_code=503, detail="Flight server not initialized")

    if flight_id not in _flight_server.flights:
        raise HTTPException(status_code=404, detail=f"Flight not found: {flight_id}")

    flight_data = _flight_server.flights[flight_id]
    schema = flight_data['schema']

    return {
        "flight_id": flight_id,
        "total_records": flight_data['total_records'],
        "schema": {
            "fields": [
                {
                    "name": name,
                    "type": str(schema.field(name).type),
                    "nullable": schema.field(name).nullable
                }
                for name in schema.names
            ]
        },
        "ticket": f"excel:{flight_id}:{{}}",
        "grpc_endpoint": f"grpc://localhost:{settings.flight_port}"
    }


@router.get("/example")
async def get_client_example():
    """
    Return Python client example code for Arrow Flight streaming
    """
    example_code = '''
# Python Arrow Flight Client Example

import pyarrow.flight as flight
import json

# 1. Connect to Flight server
client = flight.FlightClient("grpc://localhost:8815")

# 2. Prepare flight via REST API first
import requests
response = requests.post(
    "http://localhost:8000/api/v1/flight/prepare",
    params={"file_path": "/path/to/file.xlsx"}
)
flight_info = response.json()
flight_id = flight_info["flight_id"]

# 3. Stream data via gRPC (high-performance)
ticket = flight.Ticket(f"excel:{flight_id}:{{}}")
reader = client.do_get(ticket)

# 4. Process streaming data
for batch in reader:
    # batch.data is a RecordBatch
    df = batch.data.to_pandas()
    print(f"Received batch with {len(df)} rows")
    # Process data in real-time...

# 5. Or read entire stream at once
table = reader.read_all()
full_df = table.to_pandas()
print(f"Total rows: {len(full_df)}")
'''

    return JSONResponse({
        "language": "python",
        "code": example_code,
        "dependencies": ["pyarrow", "requests", "pandas"],
        "install": "pip install pyarrow requests pandas"
    })


@router.post("/action/{action_name}")
async def execute_action(action_name: str, body: dict = {}):
    """
    Control Plane: Execute custom Flight actions
    """
    if not _flight_server:
        raise HTTPException(status_code=503, detail="Flight server not initialized")

    try:
        # Create Flight action
        action = flight.Action(action_name, json.dumps(body).encode())

        # Execute and collect results
        results = []
        for result in _flight_server.do_action(None, action):
            results.append(json.loads(result.body.to_pybytes()))

        return {"results": results}

    except Exception as e:
        logger.error(f"Error executing action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
