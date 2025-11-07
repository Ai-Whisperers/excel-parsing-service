package com.customeranalysis.excel.dto;

import com.customeranalysis.excel.model.NormalizedData;
import com.customeranalysis.excel.model.WorkbookMetadata;
import lombok.Data;

/**
 * Response DTO for Excel parsing
 * Contains parsed data to be consumed by Python layer
 */
@Data
public class ParseResponse {
    private boolean success;
    private WorkbookMetadata metadata;
    private NormalizedData data;
    private long timestamp;
}
