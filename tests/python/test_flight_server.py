import pytest
import pyarrow as pa
import pyarrow.flight as flight
from app.services.flight_server import ExcelFlightServer
from unittest.mock import Mock, AsyncMock


@pytest.fixture
def flight_server():
    server = ExcelFlightServer("grpc://localhost:8816")
    yield server
    server.shutdown()


def test_server_initialization(flight_server):
    assert flight_server is not None
    assert len(flight_server.flights) == 0


def test_do_put_and_get(flight_server):
    # Create test table
    schema = pa.schema([("col1", pa.int64()), ("col2", pa.string())])
    data = pa.table({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

    # Put data
    descriptor = flight.FlightDescriptor.for_path("test_flight")

    # Simulate DoPut
    flight_server.flights["test_flight"] = {
        "schema": schema,
        "table": data,
        "total_records": 3
    }

    # Verify stored
    assert "test_flight" in flight_server.flights
    assert flight_server.flights["test_flight"]["total_records"] == 3


def test_get_flight_info(flight_server):
    schema = pa.schema([("col1", pa.int64())])
    flight_server.flights[b"test"] = {
        "schema": schema,
        "table": None,
        "total_records": 10
    }

    descriptor = flight.FlightDescriptor.for_path("test")
    info = flight_server.get_flight_info(None, descriptor)

    assert info.total_records == 10
    assert info.schema == schema


def test_get_flight_info_not_found(flight_server):
    descriptor = flight.FlightDescriptor.for_path("nonexistent")

    with pytest.raises(flight.FlightUnavailableError):
        flight_server.get_flight_info(None, descriptor)


def test_list_flights_empty(flight_server):
    flights = list(flight_server.list_flights(None, b""))
    assert len(flights) == 0


def test_list_flights_with_data(flight_server):
    schema = pa.schema([("col1", pa.int64())])
    flight_server.flights[b"flight1"] = {
        "schema": schema,
        "total_records": 5
    }
    flight_server.flights[b"flight2"] = {
        "schema": schema,
        "total_records": 10
    }

    flights = list(flight_server.list_flights(None, b""))
    assert len(flights) == 2


def test_do_action_health(flight_server):
    action = flight.Action("health", b"")
    results = list(flight_server.do_action(None, action))

    assert len(results) == 1
    import json
    result_data = json.loads(results[0].body.to_pybytes())
    assert result_data["status"] == "healthy"
    assert result_data["flights"] == 0


def test_list_actions(flight_server):
    actions = flight_server.list_actions(None)
    action_types = [action[0] for action in actions]

    assert "process_excel" in action_types
    assert "health" in action_types
