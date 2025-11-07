package com.customeranalysis.excel.service;

import com.customeranalysis.excel.dto.ParseRequest;
import com.customeranalysis.excel.dto.ParseResponse;
import com.customeranalysis.excel.service.extractor.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.ss.usermodel.Workbook;
import org.springframework.stereotype.Service;

/**
 * Core service orchestrating Excel parsing pipeline
 * Coordinates all extraction and processing components
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class ExcelParserService {

    private final WorkbookLoaderService workbookLoader;
    private final SheetEnumeratorService sheetEnumerator;
    private final CellExtractorService cellExtractor;
    private final MetadataExtractorService metadataExtractor;
    private final DataNormalizerService dataNormalizer;
    private final OutputFormatterService outputFormatter;

    public ParseResponse parseExcel(ParseRequest request) {
        log.info("Starting Excel parsing pipeline");

        try {
            // Step 1: Load workbook
            Workbook workbook = workbookLoader.loadWorkbook(request);

            // Step 2: Enumerate sheets
            var sheets = sheetEnumerator.enumerateSheets(workbook, request.getSheetName());

            // Step 3: Extract cells and regions
            var cellData = cellExtractor.extractCells(sheets, request.getRegion());

            // Step 4: Extract metadata
            var metadata = metadataExtractor.extractMetadata(workbook, sheets);

            // Step 5: Normalize and infer types
            var normalizedData = dataNormalizer.normalizeAndInferTypes(cellData);

            // Step 6: Format output (JSON for Python layer)
            ParseResponse response = outputFormatter.formatOutput(normalizedData, metadata);

            workbook.close();
            log.info("Excel parsing completed successfully");

            return response;

        } catch (Exception e) {
            log.error("Error parsing Excel file", e);
            throw new RuntimeException("Failed to parse Excel file: " + e.getMessage(), e);
        }
    }
}
