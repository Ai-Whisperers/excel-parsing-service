"""
Arrow Flight Server for high-performance streaming
Data plane: gRPC streaming for large datasets
"""

import logging
import pyarrow as pa
import pyarrow.flight as flight
from typing import Optional, Iterator
import json

from app.services.java_client import JavaLayerClient
from app.services.aggregator import DataAggregator
from app.services.arrow_formatter import ArrowFormatter
from app.config import settings

logger = logging.getLogger(__name__)


class ExcelFlightServer(flight.FlightServerBase):
    """
    Arrow Flight server for streaming Excel data
    Handles large datasets with gRPC streaming (data plane)
    """

    def __init__(self, location="grpc://0.0.0.0:8815", **kwargs):
        super(ExcelFlightServer, self).__init__(location, **kwargs)
        self.java_client = JavaLayerClient(settings.java_layer_url)
        self.aggregator = DataAggregator()
        self.arrow_formatter = ArrowFormatter()
        self.flights = {}  # In-memory flight registry
        logger.info(f"Arrow Flight server initialized at {location}")

    def _make_flight_info(self, descriptor: flight.FlightDescriptor, schema: pa.Schema, total_records: int = -1):
        """Create FlightInfo for a dataset"""
        endpoints = [flight.FlightEndpoint(descriptor.path[0].decode(), [self.location])]
        return flight.FlightInfo(schema, descriptor, endpoints, total_records, -1)

    def get_flight_info(self, context, descriptor: flight.FlightDescriptor):
        """
        Get metadata about a flight (schema, endpoints)
        Control plane: REST API calls this to get flight info
        """
        logger.info(f"GetFlightInfo called for: {descriptor.path}")

        if descriptor.path[0] not in self.flights:
            raise flight.FlightUnavailableError(f"Flight not found: {descriptor.path[0]}")

        flight_data = self.flights[descriptor.path[0]]
        return self._make_flight_info(
            descriptor,
            flight_data['schema'],
            flight_data.get('total_records', -1)
        )

    def do_put(self, context, descriptor: flight.FlightDescriptor, reader: flight.MetadataRecordBatchReader, writer):
        """
        Upload data stream (client → server)
        Used for uploading large Excel files as Arrow streams
        """
        logger.info(f"DoPut called for: {descriptor.path}")

        # Read incoming Arrow batches
        batches = []
        for chunk in reader:
            batches.append(chunk.data)

        # Store flight metadata
        table = pa.Table.from_batches(batches)
        flight_id = descriptor.path[0]
        self.flights[flight_id] = {
            'schema': table.schema,
            'table': table,
            'total_records': table.num_rows
        }

        logger.info(f"Stored flight {flight_id} with {table.num_rows} rows")

    def do_get(self, context, ticket: flight.Ticket):
        """
        Stream data (server → client)
        Data plane: High-throughput streaming of parsed Excel data
        """
        logger.info(f"DoGet called for ticket: {ticket.ticket}")

        try:
            # Parse ticket (format: "excel:{file_id}:{options_json}")
            ticket_str = ticket.ticket.decode()
            parts = ticket_str.split(':', 2)

            if parts[0] != 'excel':
                raise ValueError(f"Invalid ticket type: {parts[0]}")

            file_id = parts[1]
            options = json.loads(parts[2]) if len(parts) > 2 else {}

            # Generate Arrow stream from stored flight
            if file_id not in self.flights:
                raise flight.FlightUnavailableError(f"Flight not found: {file_id}")

            flight_data = self.flights[file_id]
            table = flight_data['table']

            # Stream table as batches
            batch_size = options.get('batch_size', 10000)
            batches = table.to_batches(max_chunksize=batch_size)

            logger.info(f"Streaming {table.num_rows} rows in batches of {batch_size}")

            return flight.RecordBatchStream(table)

        except Exception as e:
            logger.error(f"Error in DoGet: {str(e)}")
            raise flight.FlightServerError(str(e))

    def list_flights(self, context, criteria: bytes):
        """
        List available flights
        Control plane: Discover available datasets
        """
        logger.info("ListFlights called")

        for flight_id, flight_data in self.flights.items():
            descriptor = flight.FlightDescriptor.for_path(flight_id)
            yield self._make_flight_info(
                descriptor,
                flight_data['schema'],
                flight_data.get('total_records', -1)
            )

    def do_action(self, context, action: flight.Action):
        """
        Custom actions for Excel processing
        Control plane: Trigger processing jobs
        """
        logger.info(f"DoAction called: {action.type}")

        if action.type == "process_excel":
            # Parse action body
            params = json.loads(action.body.to_pybytes())
            file_path = params.get('file_path')
            sheet_name = params.get('sheet_name')

            # Process Excel file
            # This would call java_client and create a new flight
            result = {"status": "processing", "file_id": file_path}

            yield flight.Result(json.dumps(result).encode())

        elif action.type == "health":
            result = {"status": "healthy", "flights": len(self.flights)}
            yield flight.Result(json.dumps(result).encode())

        else:
            raise NotImplementedError(f"Unknown action: {action.type}")

    def list_actions(self, context):
        """
        List available actions
        """
        return [
            ("process_excel", "Process an Excel file and create a flight"),
            ("health", "Check server health"),
        ]


async def process_excel_to_flight(
    server: ExcelFlightServer,
    file_path: str,
    sheet_name: Optional[str] = None,
    region: Optional[str] = None
) -> str:
    """
    Helper function to process Excel and register as a flight
    Returns flight_id for streaming
    """
    # Call Java layer
    parse_response = await server.java_client.parse_excel_from_path(
        file_path=file_path,
        sheet_name=sheet_name,
        region=region
    )

    # Aggregate data
    aggregated_data = server.aggregator.aggregate(parse_response)

    # Convert to Arrow table
    arrow_bytes = server.arrow_formatter.format(aggregated_data)

    # Read Arrow bytes as table
    import io
    reader = pa.ipc.open_stream(io.BytesIO(arrow_bytes))
    table = reader.read_all()

    # Register flight
    flight_id = f"excel_{file_path.replace('/', '_')}"
    server.flights[flight_id] = {
        'schema': table.schema,
        'table': table,
        'total_records': table.num_rows
    }

    logger.info(f"Created flight {flight_id} with {table.num_rows} rows")
    return flight_id


def start_flight_server(host: str = "0.0.0.0", port: int = 8815):
    """Start the Arrow Flight server"""
    location = f"grpc://{host}:{port}"
    server = ExcelFlightServer(location)
    logger.info(f"Starting Arrow Flight server on {location}")
    server.serve()
    return server
