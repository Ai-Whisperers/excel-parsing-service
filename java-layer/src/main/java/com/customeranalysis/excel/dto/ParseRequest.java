package com.customeranalysis.excel.dto;

import lombok.Builder;
import lombok.Data;
import org.springframework.web.multipart.MultipartFile;

/**
 * Request DTO for Excel parsing
 */
@Data
@Builder
public class ParseRequest {
    private MultipartFile file;
    private String filePath;
    private String sheetName;
    private String region;
}
