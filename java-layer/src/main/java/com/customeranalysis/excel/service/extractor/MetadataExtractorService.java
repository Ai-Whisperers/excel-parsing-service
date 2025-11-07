package com.customeranalysis.excel.service.extractor;

import com.customeranalysis.excel.model.SheetInfo;
import com.customeranalysis.excel.model.WorkbookMetadata;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.ss.util.CellRangeAddress;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.springframework.stereotype.Service;

import java.util.*;

/**
 * Metadata Extractor
 * Gathers named ranges, comments, document properties, data validations, and conditional formatting
 */
@Service
@Slf4j
public class MetadataExtractorService {

    public WorkbookMetadata extractMetadata(Workbook workbook, List<SheetInfo> sheets) {
        log.debug("Extracting comprehensive workbook metadata");

        WorkbookMetadata metadata = new WorkbookMetadata();

        // Basic info
        metadata.setNumberOfSheets(workbook.getNumberOfSheets());
        metadata.setNumberOfNames(workbook.getNumberOfNames());

        // Extract sheet information
        Map<String, Integer> sheetMap = new HashMap<>();
        Map<String, Map<String, Object>> sheetMetadata = new HashMap<>();

        for (SheetInfo sheetInfo : sheets) {
            sheetMap.put(sheetInfo.getName(), sheetInfo.getIndex());

            Map<String, Object> sheetMeta = new HashMap<>();
            Sheet sheet = sheetInfo.getSheet();

            // Sheet visibility
            sheetMeta.put("visible", !workbook.isSheetHidden(sheetInfo.getIndex()));
            sheetMeta.put("veryHidden", workbook.isSheetVeryHidden(sheetInfo.getIndex()));

            // Row/column counts
            sheetMeta.put("firstRowNum", sheet.getFirstRowNum());
            sheetMeta.put("lastRowNum", sheet.getLastRowNum());
            sheetMeta.put("physicalNumberOfRows", sheet.getPhysicalNumberOfRows());

            // Default sizes
            sheetMeta.put("defaultRowHeight", sheet.getDefaultRowHeight());
            sheetMeta.put("defaultColumnWidth", sheet.getDefaultColumnWidth());

            // Protection
            sheetMeta.put("protected", sheet.getProtect());

            // Merged regions count
            sheetMeta.put("numMergedRegions", sheet.getNumMergedRegions());

            // Comments count
            int commentCount = countComments(sheet);
            sheetMeta.put("numComments", commentCount);

            // Hyperlinks count
            int hyperlinkCount = countHyperlinks(sheet);
            sheetMeta.put("numHyperlinks", hyperlinkCount);

            sheetMetadata.put(sheetInfo.getName(), sheetMeta);
        }

        metadata.setSheets(sheetMap);
        metadata.setSheetMetadata(sheetMetadata);

        // Extract named ranges
        List<Map<String, Object>> namedRanges = extractNamedRanges(workbook);
        metadata.setNamedRanges(namedRanges);

        // Extract document properties
        Map<String, Object> documentProperties = extractDocumentProperties(workbook);
        metadata.setDocumentProperties(documentProperties);

        // Extract custom properties
        Map<String, Object> customProperties = extractCustomProperties(workbook);
        if (!customProperties.isEmpty()) {
            metadata.setCustomProperties(customProperties);
        }

        // Extract workbook-level info
        metadata.setWorkbookType(workbook instanceof XSSFWorkbook ? "XLSX" : "XLS");
        metadata.setNumberOfFonts(workbook.getNumberOfFonts());
        metadata.setNumberOfCellStyles(workbook.getNumCellStyles());

        // Extract active sheet
        metadata.setActiveSheetIndex(workbook.getActiveSheetIndex());
        String activeSheetName = workbook.getSheetAt(workbook.getActiveSheetIndex()).getSheetName();
        metadata.setActiveSheetName(activeSheetName);

        log.info("Extracted metadata: {} sheets, {} named ranges, {} document properties",
                sheets.size(), namedRanges.size(), documentProperties.size());

        return metadata;
    }

    private int countComments(Sheet sheet) {
        int count = 0;
        for (Row row : sheet) {
            for (Cell cell : row) {
                if (cell.getCellComment() != null) {
                    count++;
                }
            }
        }
        return count;
    }

    private int countHyperlinks(Sheet sheet) {
        int count = 0;
        for (Row row : sheet) {
            for (Cell cell : row) {
                if (cell.getHyperlink() != null) {
                    count++;
                }
            }
        }
        return count;
    }

    private List<Map<String, Object>> extractNamedRanges(Workbook workbook) {
        List<Map<String, Object>> namedRanges = new ArrayList<>();

        List<? extends Name> allNames = workbook.getAllNames();
        for (Name name : allNames) {
            try {
                Map<String, Object> nameInfo = new HashMap<>();

                nameInfo.put("name", name.getNameName());
                nameInfo.put("formula", name.getRefersToFormula());
                nameInfo.put("sheetIndex", name.getSheetIndex());

                if (name.getSheetIndex() >= 0) {
                    nameInfo.put("sheetName", workbook.getSheetName(name.getSheetIndex()));
                } else {
                    nameInfo.put("scope", "workbook");
                }

                nameInfo.put("comment", name.getComment());
                nameInfo.put("function", name.isFunctionName());
                nameInfo.put("deleted", name.isDeleted());

                namedRanges.add(nameInfo);
            } catch (Exception e) {
                log.warn("Error extracting named range at index {}: {}", i, e.getMessage());
            }
        }

        return namedRanges;
    }

    private Map<String, Object> extractDocumentProperties(Workbook workbook) {
        Map<String, Object> props = new HashMap<>();

        try {
            if (workbook instanceof XSSFWorkbook) {
                XSSFWorkbook xssfWorkbook = (XSSFWorkbook) workbook;
                var coreProps = xssfWorkbook.getProperties().getCoreProperties();

                if (coreProps != null) {
                    props.put("creator", coreProps.getCreator());
                    props.put("title", coreProps.getTitle());
                    props.put("subject", coreProps.getSubject());
                    props.put("description", coreProps.getDescription());
                    props.put("keywords", coreProps.getKeywords());
                    props.put("category", coreProps.getCategory());
                    props.put("revision", coreProps.getRevision());
                    props.put("lastModifiedBy", coreProps.getUnderlyingProperties().getLastModifiedByProperty());

                    // Dates
                    if (coreProps.getCreated() != null) {
                        props.put("created", coreProps.getCreated().toString());
                    }
                    if (coreProps.getModified() != null) {
                        props.put("modified", coreProps.getModified().toString());
                    }
                }
            } else if (workbook instanceof HSSFWorkbook) {
                HSSFWorkbook hssfWorkbook = (HSSFWorkbook) workbook;
                var summaryInfo = hssfWorkbook.getSummaryInformation();

                if (summaryInfo != null) {
                    props.put("title", summaryInfo.getTitle());
                    props.put("author", summaryInfo.getAuthor());
                    props.put("subject", summaryInfo.getSubject());
                    props.put("keywords", summaryInfo.getKeywords());
                    props.put("comments", summaryInfo.getComments());
                    props.put("applicationName", summaryInfo.getApplicationName());
                    props.put("lastAuthor", summaryInfo.getLastAuthor());

                    if (summaryInfo.getCreateDateTime() != null) {
                        props.put("created", summaryInfo.getCreateDateTime().toString());
                    }
                    if (summaryInfo.getLastSaveDateTime() != null) {
                        props.put("modified", summaryInfo.getLastSaveDateTime().toString());
                    }
                }
            }
        } catch (Exception e) {
            log.warn("Error extracting document properties: {}", e.getMessage());
        }

        return props;
    }

    private Map<String, Object> extractCustomProperties(Workbook workbook) {
        Map<String, Object> customProps = new HashMap<>();

        try {
            if (workbook instanceof XSSFWorkbook) {
                XSSFWorkbook xssfWorkbook = (XSSFWorkbook) workbook;
                var customProperties = xssfWorkbook.getProperties().getCustomProperties();

                if (customProperties != null) {
                    var props = customProperties.getUnderlyingProperties();
                    if (props != null && props.getPropertyList() != null) {
                        for (var prop : props.getPropertyList()) {
                            try {
                                String name = prop.getName();
                                Object value = null;

                                if (prop.isSetLpwstr()) {
                                    value = prop.getLpwstr();
                                } else if (prop.isSetI4()) {
                                    value = prop.getI4();
                                } else if (prop.isSetR8()) {
                                    value = prop.getR8();
                                } else if (prop.isSetBool()) {
                                    value = prop.getBool();
                                } else if (prop.isSetFiletime()) {
                                    value = prop.getFiletime().toString();
                                }

                                if (name != null && value != null) {
                                    customProps.put(name, value);
                                }
                            } catch (Exception e) {
                                log.warn("Error extracting custom property: {}", e.getMessage());
                            }
                        }
                    }
                }
            }
        } catch (Exception e) {
            log.warn("Error extracting custom properties: {}", e.getMessage());
        }

        return customProps;
    }
}
