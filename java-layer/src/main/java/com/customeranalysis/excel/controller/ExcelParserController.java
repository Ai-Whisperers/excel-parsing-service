package com.customeranalysis.excel.controller;

import com.customeranalysis.excel.dto.ParseRequest;
import com.customeranalysis.excel.dto.ParseResponse;
import com.customeranalysis.excel.service.ExcelParserService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

/**
 * REST controller for Excel parsing operations
 * Exposes endpoints consumed by Python aggregation layer
 */
@RestController
@RequestMapping("/api/v1/excel")
@RequiredArgsConstructor
@Slf4j
public class ExcelParserController {

    private final ExcelParserService parserService;

    /**
     * Parse Excel file from multipart upload
     * Returns raw parsed data for Python layer to aggregate
     */
    @PostMapping(value = "/parse", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<ParseResponse> parseExcelFile(
            @RequestParam("file") MultipartFile file,
            @RequestParam(required = false) String sheetName,
            @RequestParam(required = false) String region) {

        log.info("Received Excel file: {}, size: {} bytes", file.getOriginalFilename(), file.getSize());

        ParseRequest request = ParseRequest.builder()
                .file(file)
                .sheetName(sheetName)
                .region(region)
                .build();

        ParseResponse response = parserService.parseExcel(request);
        return ResponseEntity.ok(response);
    }

    /**
     * Parse Excel file from path (local or cloud storage)
     */
    @PostMapping("/parse-from-path")
    public ResponseEntity<ParseResponse> parseExcelFromPath(
            @Valid @RequestBody ParseRequest request) {

        log.info("Parsing Excel from path: {}", request.getFilePath());
        ParseResponse response = parserService.parseExcel(request);
        return ResponseEntity.ok(response);
    }

    /**
     * Health check endpoint
     */
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("Java Layer: Excel Parser Service is running");
    }
}
