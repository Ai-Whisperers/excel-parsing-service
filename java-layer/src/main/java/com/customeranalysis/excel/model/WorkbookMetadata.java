package com.customeranalysis.excel.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Data;
import java.util.List;
import java.util.Map;

/**
 * Comprehensive workbook metadata model
 */
@Data
@JsonInclude(JsonInclude.Include.NON_NULL)
public class WorkbookMetadata {
    // Basic counts
    private int numberOfSheets;
    private int numberOfNames;
    private int numberOfFonts;
    private int numberOfCellStyles;

    // Sheet information
    private Map<String, Integer> sheets;  // sheet name -> index
    private Map<String, Map<String, Object>> sheetMetadata;  // detailed metadata per sheet

    // Active sheet
    private int activeSheetIndex;
    private String activeSheetName;

    // Named ranges
    private List<Map<String, Object>> namedRanges;

    // Document properties
    private Map<String, Object> documentProperties;
    private Map<String, Object> customProperties;

    // Workbook type
    private String workbookType;  // "XLSX" or "XLS"
}
