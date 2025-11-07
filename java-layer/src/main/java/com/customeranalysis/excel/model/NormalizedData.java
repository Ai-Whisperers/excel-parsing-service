package com.customeranalysis.excel.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Data;
import java.util.List;
import java.util.Map;

/**
 * Normalized data model with statistics and type inference
 */
@Data
@JsonInclude(JsonInclude.Include.NON_NULL)
public class NormalizedData {
    private Map<String, List<CellData>> sheetData;
    private int totalCells;
    private Map<String, Map<String, Object>> statistics;  // per-sheet statistics
}
