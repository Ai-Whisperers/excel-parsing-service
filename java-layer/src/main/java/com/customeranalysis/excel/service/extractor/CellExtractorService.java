package com.customeranalysis.excel.service.extractor;

import com.customeranalysis.excel.model.CellData;
import com.customeranalysis.excel.model.SheetInfo;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.ss.util.CellRangeAddress;
import org.apache.poi.ss.util.CellReference;
import org.springframework.stereotype.Service;

import java.text.SimpleDateFormat;
import java.util.*;

/**
 * Cell & Region Extractor
 * Reads rows/cells, detects data blocks, merged cells, formulas, rich text, and styles
 */
@Service
@Slf4j
public class CellExtractorService {

    private static final SimpleDateFormat DATE_FORMAT = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss");

    public List<CellData> extractCells(List<SheetInfo> sheets, String regionFilter) {
        log.debug("Extracting cells with region filter: {}", regionFilter);

        List<CellData> allCells = new ArrayList<>();

        for (SheetInfo sheetInfo : sheets) {
            Sheet sheet = sheetInfo.getSheet();

            // Build merged cell map for this sheet
            Map<String, CellRangeAddress> mergedRegions = buildMergedCellMap(sheet);

            // Parse region filter if provided
            CellRangeAddress filterRange = parseRegionFilter(regionFilter);

            for (Row row : sheet) {
                if (filterRange != null && !isRowInRange(row.getRowNum(), filterRange)) {
                    continue;
                }

                for (Cell cell : row) {
                    if (filterRange != null && !isCellInRange(cell, filterRange)) {
                        continue;
                    }

                    CellData cellData = extractCellData(cell, sheetInfo.getName(), mergedRegions);
                    allCells.add(cellData);
                }
            }
        }

        log.info("Extracted {} cells", allCells.size());
        return allCells;
    }

    private Map<String, CellRangeAddress> buildMergedCellMap(Sheet sheet) {
        Map<String, CellRangeAddress> mergedMap = new HashMap<>();
        int numMerged = sheet.getNumMergedRegions();

        for (int i = 0; i < numMerged; i++) {
            CellRangeAddress range = sheet.getMergedRegion(i);
            for (int row = range.getFirstRow(); row <= range.getLastRow(); row++) {
                for (int col = range.getFirstColumn(); col <= range.getLastColumn(); col++) {
                    String key = row + ":" + col;
                    mergedMap.put(key, range);
                }
            }
        }

        return mergedMap;
    }

    private CellRangeAddress parseRegionFilter(String regionFilter) {
        if (regionFilter == null || regionFilter.trim().isEmpty()) {
            return null;
        }

        try {
            return CellRangeAddress.valueOf(regionFilter);
        } catch (Exception e) {
            log.warn("Invalid region filter: {}", regionFilter, e);
            return null;
        }
    }

    private boolean isRowInRange(int rowNum, CellRangeAddress range) {
        return rowNum >= range.getFirstRow() && rowNum <= range.getLastRow();
    }

    private boolean isCellInRange(Cell cell, CellRangeAddress range) {
        return cell.getRowIndex() >= range.getFirstRow()
            && cell.getRowIndex() <= range.getLastRow()
            && cell.getColumnIndex() >= range.getFirstColumn()
            && cell.getColumnIndex() <= range.getLastColumn();
    }

    private CellData extractCellData(Cell cell, String sheetName, Map<String, CellRangeAddress> mergedRegions) {
        CellData data = new CellData();
        data.setSheetName(sheetName);
        data.setRowIndex(cell.getRowIndex());
        data.setColumnIndex(cell.getColumnIndex());

        // Cell reference (e.g., "A1")
        String cellRef = new CellReference(cell).formatAsString();
        data.setCellReference(cellRef);

        // Check if cell is part of merged region
        String mergeKey = cell.getRowIndex() + ":" + cell.getColumnIndex();
        CellRangeAddress mergedRegion = mergedRegions.get(mergeKey);
        if (mergedRegion != null) {
            data.setMerged(true);
            data.setMergeRegion(mergedRegion.formatAsString());

            // Check if this is the master cell (top-left of merged region)
            boolean isMasterCell = cell.getRowIndex() == mergedRegion.getFirstRow()
                                && cell.getColumnIndex() == mergedRegion.getFirstColumn();
            data.setMergedCellMaster(isMasterCell);
        }

        // Extract cell type and value
        CellType cellType = cell.getCellType();
        data.setCellType(cellType.toString());

        try {
            switch (cellType) {
                case STRING:
                    extractStringCell(cell, data);
                    break;
                case NUMERIC:
                    extractNumericCell(cell, data);
                    break;
                case BOOLEAN:
                    data.setValue(cell.getBooleanCellValue());
                    break;
                case FORMULA:
                    extractFormulaCell(cell, data);
                    break;
                case BLANK:
                    data.setValue(null);
                    break;
                case ERROR:
                    data.setValue("ERROR:" + cell.getErrorCellValue());
                    data.setCellType("ERROR");
                    break;
                default:
                    data.setValue(cell.toString());
            }
        } catch (Exception e) {
            log.warn("Error extracting cell value at {}: {}", cellRef, e.getMessage());
            data.setValue(null);
            data.setError(e.getMessage());
        }

        // Extract style information
        extractStyleInfo(cell, data);

        // Extract comment if present
        extractComment(cell, data);

        // Extract hyperlink if present
        extractHyperlink(cell, data);

        return data;
    }

    private void extractStringCell(Cell cell, CellData data) {
        RichTextString richText = cell.getRichStringCellValue();
        String value = richText.getString();
        data.setValue(value);

        // Check for rich text formatting
        if (richText.numFormattingRuns() > 0) {
            data.setRichText(true);
            // Store formatting information
            Map<String, Object> richTextInfo = new HashMap<>();
            richTextInfo.put("numRuns", richText.numFormattingRuns());
            data.setRichTextFormatting(richTextInfo);
        }
    }

    private void extractNumericCell(Cell cell, CellData data) {
        if (DateUtil.isCellDateFormatted(cell)) {
            // Handle date/time values
            try {
                Date dateValue = cell.getDateCellValue();
                data.setValue(DATE_FORMAT.format(dateValue));
                data.setCellType("DATE");
                data.setDateValue(dateValue);
            } catch (Exception e) {
                log.warn("Error parsing date value: {}", e.getMessage());
                data.setValue(cell.getNumericCellValue());
            }
        } else {
            double numericValue = cell.getNumericCellValue();

            // Check if it's a whole number
            if (numericValue == Math.floor(numericValue) && !Double.isInfinite(numericValue)) {
                data.setValue((long) numericValue);
            } else {
                data.setValue(numericValue);
            }
        }
    }

    private void extractFormulaCell(Cell cell, CellData data) {
        String formula = cell.getCellFormula();
        data.setFormula(formula);
        data.setCellType("FORMULA");

        // Try to get the cached/calculated value
        try {
            CellType cachedType = cell.getCachedFormulaResultType();

            switch (cachedType) {
                case STRING:
                    data.setValue(cell.getStringCellValue());
                    data.setFormulaResultType("STRING");
                    break;
                case NUMERIC:
                    if (DateUtil.isCellDateFormatted(cell)) {
                        data.setValue(DATE_FORMAT.format(cell.getDateCellValue()));
                        data.setFormulaResultType("DATE");
                    } else {
                        data.setValue(cell.getNumericCellValue());
                        data.setFormulaResultType("NUMERIC");
                    }
                    break;
                case BOOLEAN:
                    data.setValue(cell.getBooleanCellValue());
                    data.setFormulaResultType("BOOLEAN");
                    break;
                case ERROR:
                    data.setValue("ERROR:" + cell.getErrorCellValue());
                    data.setFormulaResultType("ERROR");
                    break;
                default:
                    data.setValue(null);
            }
        } catch (Exception e) {
            log.warn("Error evaluating formula at {}: {}", data.getCellReference(), e.getMessage());
            data.setValue(null);
            data.setError("Formula evaluation error: " + e.getMessage());
        }
    }

    private void extractStyleInfo(Cell cell, CellData data) {
        CellStyle style = cell.getCellStyle();
        if (style == null) {
            return;
        }

        Map<String, Object> styleInfo = new HashMap<>();

        // Font information
        Font font = cell.getSheet().getWorkbook().getFontAt(style.getFontIndex());
        if (font != null) {
            Map<String, Object> fontInfo = new HashMap<>();
            fontInfo.put("name", font.getFontName());
            fontInfo.put("size", font.getFontHeightInPoints());
            fontInfo.put("bold", font.getBold());
            fontInfo.put("italic", font.getItalic());
            fontInfo.put("underline", font.getUnderline());
            fontInfo.put("color", font.getColor());
            styleInfo.put("font", fontInfo);
        }

        // Alignment
        styleInfo.put("horizontalAlignment", style.getAlignment().toString());
        styleInfo.put("verticalAlignment", style.getVerticalAlignment().toString());

        // Background color
        styleInfo.put("fillPattern", style.getFillPattern().toString());
        styleInfo.put("fillForegroundColor", style.getFillForegroundColor());

        // Borders
        styleInfo.put("borderTop", style.getBorderTop().toString());
        styleInfo.put("borderBottom", style.getBorderBottom().toString());
        styleInfo.put("borderLeft", style.getBorderLeft().toString());
        styleInfo.put("borderRight", style.getBorderRight().toString());

        // Number format
        String dataFormatString = style.getDataFormatString();
        if (dataFormatString != null && !dataFormatString.isEmpty()) {
            styleInfo.put("numberFormat", dataFormatString);
        }

        data.setStyleInfo(styleInfo);
    }

    private void extractComment(Cell cell, CellData data) {
        Comment comment = cell.getCellComment();
        if (comment != null) {
            RichTextString commentText = comment.getString();
            data.setComment(commentText.getString());

            if (comment.getAuthor() != null) {
                data.setCommentAuthor(comment.getAuthor());
            }
        }
    }

    private void extractHyperlink(Cell cell, CellData data) {
        Hyperlink hyperlink = cell.getHyperlink();
        if (hyperlink != null) {
            data.setHyperlink(hyperlink.getAddress());
            data.setHyperlinkType(hyperlink.getType().toString());
        }
    }
}
