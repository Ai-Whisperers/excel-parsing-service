import pytest
from app.services.aggregator import DataAggregator


@pytest.fixture
def aggregator():
    return DataAggregator()


@pytest.fixture
def sample_parse_response():
    return {
        "metadata": {
            "fileName": "test.xlsx",
            "sheetCount": 1
        },
        "data": {
            "sheetData": {
                "Sheet1": [
                    {"rowIndex": 0, "columnIndex": 0, "value": "Name", "cellType": "STRING"},
                    {"rowIndex": 0, "columnIndex": 1, "value": "Age", "cellType": "STRING"},
                    {"rowIndex": 1, "columnIndex": 0, "value": "John", "cellType": "STRING"},
                    {"rowIndex": 1, "columnIndex": 1, "value": 30, "cellType": "NUMERIC"}
                ]
            },
            "statistics": {}
        },
        "timestamp": "2025-11-08T00:00:00"
    }


def test_aggregate_basic(aggregator, sample_parse_response):
    result = aggregator.aggregate(sample_parse_response)

    assert "metadata" in result
    assert "sheets" in result
    assert "Sheet1" in result["sheets"]

    sheet = result["sheets"]["Sheet1"]
    assert sheet["rowCount"] == 1
    assert sheet["columnCount"] == 2
    assert sheet["hasHeader"] is True


def test_aggregate_empty_sheet(aggregator):
    response = {
        "metadata": {},
        "data": {"sheetData": {"Empty": []}},
        "timestamp": "2025-11-08T00:00:00"
    }

    result = aggregator.aggregate(response)
    sheet = result["sheets"]["Empty"]

    assert sheet["rowCount"] == 0
    assert sheet["columnCount"] == 0


def test_cells_to_table_with_formulas(aggregator):
    cells = [
        {"rowIndex": 0, "columnIndex": 0, "value": "Result", "cellType": "STRING"},
        {"rowIndex": 1, "columnIndex": 0, "value": 100, "cellType": "NUMERIC",
         "formula": "=SUM(A2:A10)", "formulaResultType": "NUMERIC"}
    ]

    table = aggregator._cells_to_table(cells)

    assert table["cellMetadata"][1][0]["formula"] == "=SUM(A2:A10)"


def test_extract_rich_metadata(aggregator):
    cells = [
        {"rowIndex": 0, "columnIndex": 0, "value": "Link", "hyperlink": "http://example.com"},
        {"rowIndex": 1, "columnIndex": 0, "value": "Note", "comment": "Important"},
        {"rowIndex": 2, "columnIndex": 0, "value": 100, "formula": "=A1+A2"}
    ]

    meta = aggregator._extract_rich_metadata(cells)

    assert len(meta["hyperlinks"]) == 1
    assert len(meta["comments"]) == 1
    assert len(meta["formulas"]) == 1
    assert meta["counts"]["hyperlinks"] == 1


def test_compute_aggregated_statistics(aggregator):
    table = {"rowCount": 10, "columnCount": 5}
    cells = [
        {"cellType": "NUMERIC", "value": 10},
        {"cellType": "NUMERIC", "value": 20},
        {"cellType": "STRING", "value": "test"},
        {"cellType": "NUMERIC", "value": None}
    ]

    stats = aggregator._compute_aggregated_statistics(table, cells)

    assert stats["rowCount"] == 10
    assert stats["columnCount"] == 5
    assert stats["totalCells"] == 50
    assert "numericSummary" in stats
    assert stats["numericSummary"]["count"] == 2
    assert stats["numericSummary"]["min"] == 10
    assert stats["numericSummary"]["max"] == 20


def test_detect_header_row_true(aggregator):
    grid = [
        ["Name", "Age", "City"],
        [25, 30, "NYC"],
        [30, 40, "LA"]
    ]
    cells = [
        {"rowIndex": 0, "columnIndex": 0, "cellType": "STRING"},
        {"rowIndex": 0, "columnIndex": 1, "cellType": "STRING"},
        {"rowIndex": 0, "columnIndex": 2, "cellType": "STRING"}
    ]

    result = aggregator._detect_header_row(grid, cells)
    assert result is True


def test_detect_header_row_false(aggregator):
    grid = [
        [1, 2, 3],
        [4, 5, 6]
    ]
    cells = [
        {"rowIndex": 0, "columnIndex": 0, "cellType": "NUMERIC"},
        {"rowIndex": 0, "columnIndex": 1, "cellType": "NUMERIC"},
        {"rowIndex": 0, "columnIndex": 2, "cellType": "NUMERIC"}
    ]

    result = aggregator._detect_header_row(grid, cells)
    assert result is False
