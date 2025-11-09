import pytest
import pyarrow as pa
import io
from app.services.arrow_formatter import ArrowFormatter


@pytest.fixture
def formatter():
    return ArrowFormatter()


@pytest.fixture
def sample_aggregated_data():
    return {
        "metadata": {"fileName": "test.xlsx"},
        "sheets": {
            "Sheet1": {
                "columns": ["Name", "Age"],
                "rows": [["John", 30], ["Jane", 25]],
                "rowCount": 2,
                "columnCount": 2
            }
        }
    }


def test_format_creates_valid_arrow(formatter, sample_aggregated_data):
    result = formatter.format(sample_aggregated_data)

    assert isinstance(result, bytes)

    # Verify it's valid Arrow format
    reader = pa.ipc.open_stream(io.BytesIO(result))
    table = reader.read_all()

    assert table.num_rows == 2
    assert table.num_columns == 2
    assert "Name" in table.column_names
    assert "Age" in table.column_names


def test_format_multiple_sheets(formatter):
    data = {
        "metadata": {},
        "sheets": {
            "Sheet1": {
                "columns": ["A", "B"],
                "rows": [[1, 2]],
                "rowCount": 1,
                "columnCount": 2
            },
            "Sheet2": {
                "columns": ["X", "Y"],
                "rows": [[10, 20]],
                "rowCount": 1,
                "columnCount": 2
            }
        }
    }

    result = formatter.format(data)
    reader = pa.ipc.open_stream(io.BytesIO(result))
    table = reader.read_all()

    assert table.num_rows == 2  # Combined rows


def test_format_empty_sheet(formatter):
    data = {
        "metadata": {},
        "sheets": {
            "Empty": {
                "columns": [],
                "rows": [],
                "rowCount": 0,
                "columnCount": 0
            }
        }
    }

    result = formatter.format(data)
    reader = pa.ipc.open_stream(io.BytesIO(result))
    table = reader.read_all()

    assert table.num_rows == 0


def test_format_mixed_types(formatter):
    data = {
        "metadata": {},
        "sheets": {
            "Mixed": {
                "columns": ["String", "Number", "Bool", "None"],
                "rows": [
                    ["text", 42, True, None],
                    ["more", 3.14, False, None]
                ],
                "rowCount": 2,
                "columnCount": 4
            }
        }
    }

    result = formatter.format(data)
    reader = pa.ipc.open_stream(io.BytesIO(result))
    table = reader.read_all()

    assert table.num_rows == 2
    assert table.num_columns == 4
