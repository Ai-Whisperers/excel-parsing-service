package com.customeranalysis.excel.service.extractor;

import com.customeranalysis.excel.model.SheetInfo;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.ss.usermodel.Workbook;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

/**
 * Sheet Enumerator
 * Iterates over sheets and collects sheet-level metadata
 */
@Service
@Slf4j
public class SheetEnumeratorService {

    public List<SheetInfo> enumerateSheets(Workbook workbook, String sheetNameFilter) {
        log.debug("Enumerating sheets");

        List<SheetInfo> sheets = new ArrayList<>();

        for (int i = 0; i < workbook.getNumberOfSheets(); i++) {
            Sheet sheet = workbook.getSheetAt(i);
            String sheetName = sheet.getSheetName();

            if (sheetNameFilter != null && !sheetNameFilter.isEmpty()
                && !sheetName.equals(sheetNameFilter)) {
                continue;
            }

            SheetInfo info = SheetInfo.builder()
                    .index(i)
                    .name(sheetName)
                    .sheet(sheet)
                    .firstRowNum(sheet.getFirstRowNum())
                    .lastRowNum(sheet.getLastRowNum())
                    .build();

            sheets.add(info);
            log.debug("Sheet: {} (rows: {} - {})", sheetName, info.getFirstRowNum(), info.getLastRowNum());
        }

        log.info("Enumerated {} sheets", sheets.size());
        return sheets;
    }
}
