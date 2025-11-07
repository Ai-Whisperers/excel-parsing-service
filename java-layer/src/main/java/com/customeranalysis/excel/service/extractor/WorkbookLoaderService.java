package com.customeranalysis.excel.service.extractor;

import com.customeranalysis.excel.dto.ParseRequest;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.ss.usermodel.Workbook;
import org.apache.poi.ss.usermodel.WorkbookFactory;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.InputStream;

/**
 * POI Workbook Loader
 * Handles loading .xls/.xlsx files with password protection and encoding support
 */
@Service
@Slf4j
public class WorkbookLoaderService {

    public Workbook loadWorkbook(ParseRequest request) throws Exception {
        log.debug("Loading workbook");

        Workbook workbook;

        if (request.getFile() != null) {
            // Load from multipart file
            try (InputStream is = request.getFile().getInputStream()) {
                workbook = WorkbookFactory.create(is);
            }
        } else if (request.getFilePath() != null) {
            // Load from file path
            File file = new File(request.getFilePath());
            workbook = WorkbookFactory.create(file);
        } else {
            throw new IllegalArgumentException("Either file or filePath must be provided");
        }

        log.info("Workbook loaded successfully with {} sheets", workbook.getNumberOfSheets());
        return workbook;
    }
}
