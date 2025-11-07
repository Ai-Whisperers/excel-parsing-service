package com.customeranalysis.excel.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Builder;
import lombok.Data;
import org.apache.poi.ss.usermodel.Sheet;

/**
 * Sheet information model
 */
@Data
@Builder
public class SheetInfo {
    private int index;
    private String name;

    @JsonIgnore
    private Sheet sheet;

    private int firstRowNum;
    private int lastRowNum;
}
