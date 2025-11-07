"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class ExcelProcessRequest(BaseModel):
    file_path: str
    sheet_name: Optional[str] = None
    region: Optional[str] = None
    output_format: str = Field(default="json", pattern="^(json|arrow)$")
    aggregate: bool = True


class CellData(BaseModel):
    sheetName: str
    rowIndex: int
    columnIndex: int
    cellType: str
    value: Any
    formula: Optional[str] = None


class WorkbookMetadata(BaseModel):
    numberOfSheets: int
    numberOfNames: int
    sheets: Dict[str, int]


class NormalizedData(BaseModel):
    sheetData: Dict[str, List[CellData]]
    totalCells: int


class ParseResponse(BaseModel):
    success: bool
    metadata: WorkbookMetadata
    data: NormalizedData
    timestamp: int
