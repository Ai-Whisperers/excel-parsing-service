package com.customeranalysis.excel.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Data;

import java.util.Date;
import java.util.Map;

/**
 * Cell data model with comprehensive Excel metadata
 */
@Data
@JsonInclude(JsonInclude.Include.NON_NULL)
public class CellData {
    // Basic cell information
    private String sheetName;
    private int rowIndex;
    private int columnIndex;
    private String cellReference;  // e.g., "A1"
    private String cellType;
    private Object value;

    // Formula information
    private String formula;
    private String formulaResultType;

    // Merged cell information
    private Boolean merged;
    private String mergeRegion;  // e.g., "A1:B2"
    private Boolean mergedCellMaster;  // true if this is the top-left cell of merged region

    // Rich text
    private Boolean richText;
    private Map<String, Object> richTextFormatting;

    // Date handling
    private Date dateValue;

    // Style information
    private Map<String, Object> styleInfo;

    // Comment
    private String comment;
    private String commentAuthor;

    // Hyperlink
    private String hyperlink;
    private String hyperlinkType;

    // Error handling
    private String error;
}
