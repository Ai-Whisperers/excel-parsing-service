package com.customeranalysis.excel.service.extractor;

import com.customeranalysis.excel.model.CellData;
import com.customeranalysis.excel.model.NormalizedData;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Data Normalizer & Type Inferencer
 * Standardizes values, infers types per column, validates data, and provides quality metrics
 */
@Service
@Slf4j
public class DataNormalizerService {

    private static final int MIN_SAMPLE_SIZE = 5;  // Minimum cells to infer column type
    private static final double TYPE_CONFIDENCE_THRESHOLD = 0.8;  // 80% of cells must match type

    public NormalizedData normalizeAndInferTypes(List<CellData> cellData) {
        log.debug("Normalizing data and inferring types");

        NormalizedData normalized = new NormalizedData();

        // Group cells by sheet
        Map<String, List<CellData>> bySheet = new HashMap<>();
        for (CellData cell : cellData) {
            bySheet.computeIfAbsent(cell.getSheetName(), k -> new ArrayList<>()).add(cell);
        }

        // Process each sheet
        Map<String, Map<String, Object>> sheetStats = new HashMap<>();
        for (Map.Entry<String, List<CellData>> entry : bySheet.entrySet()) {
            String sheetName = entry.getKey();
            List<CellData> cells = entry.getValue();

            // Calculate sheet statistics
            Map<String, Object> stats = calculateSheetStatistics(cells);
            sheetStats.put(sheetName, stats);

            // Infer column types
            Map<Integer, String> columnTypes = inferColumnTypes(cells);
            stats.put("columnTypes", columnTypes);

            // Detect data quality issues
            List<String> qualityIssues = detectQualityIssues(cells);
            if (!qualityIssues.isEmpty()) {
                stats.put("qualityIssues", qualityIssues);
            }
        }

        normalized.setSheetData(bySheet);
        normalized.setTotalCells(cellData.size());
        normalized.setStatistics(sheetStats);

        log.info("Normalized {} cells across {} sheets with type inference", cellData.size(), bySheet.size());
        return normalized;
    }

    private Map<String, Object> calculateSheetStatistics(List<CellData> cells) {
        Map<String, Object> stats = new HashMap<>();

        int totalCells = cells.size();
        int nullCells = 0;
        int errorCells = 0;
        int formulaCells = 0;
        int mergedCells = 0;

        // Count cell types
        Map<String, Integer> typeCounts = new HashMap<>();

        // Track value ranges for numeric columns
        Map<Integer, Double> minValues = new HashMap<>();
        Map<Integer, Double> maxValues = new HashMap<>();

        for (CellData cell : cells) {
            if (cell.getValue() == null) {
                nullCells++;
            }

            if (cell.getError() != null) {
                errorCells++;
            }

            if (cell.getFormula() != null) {
                formulaCells++;
            }

            if (Boolean.TRUE.equals(cell.getMerged())) {
                mergedCells++;
            }

            // Count cell types
            String type = cell.getCellType();
            typeCounts.put(type, typeCounts.getOrDefault(type, 0) + 1);

            // Track numeric ranges
            if ("NUMERIC".equals(type) && cell.getValue() instanceof Number) {
                double value = ((Number) cell.getValue()).doubleValue();
                int colIndex = cell.getColumnIndex();

                minValues.merge(colIndex, value, Math::min);
                maxValues.merge(colIndex, value, Math::max);
            }
        }

        stats.put("totalCells", totalCells);
        stats.put("nullCells", nullCells);
        stats.put("errorCells", errorCells);
        stats.put("formulaCells", formulaCells);
        stats.put("mergedCells", mergedCells);
        stats.put("nullPercentage", totalCells > 0 ? (double) nullCells / totalCells * 100 : 0);
        stats.put("typeCounts", typeCounts);

        if (!minValues.isEmpty()) {
            stats.put("numericRanges", buildNumericRanges(minValues, maxValues));
        }

        return stats;
    }

    private Map<String, Object> buildNumericRanges(Map<Integer, Double> minValues, Map<Integer, Double> maxValues) {
        Map<String, Object> ranges = new HashMap<>();

        for (Integer colIndex : minValues.keySet()) {
            Map<String, Double> range = new HashMap<>();
            range.put("min", minValues.get(colIndex));
            range.put("max", maxValues.get(colIndex));
            ranges.put("column_" + colIndex, range);
        }

        return ranges;
    }

    private Map<Integer, String> inferColumnTypes(List<CellData> cells) {
        // Group cells by column
        Map<Integer, List<CellData>> byColumn = cells.stream()
                .collect(Collectors.groupingBy(CellData::getColumnIndex));

        Map<Integer, String> columnTypes = new HashMap<>();

        for (Map.Entry<Integer, List<CellData>> entry : byColumn.entrySet()) {
            int columnIndex = entry.getKey();
            List<CellData> columnCells = entry.getValue();

            String inferredType = inferSingleColumnType(columnCells);
            columnTypes.put(columnIndex, inferredType);
        }

        return columnTypes;
    }

    private String inferSingleColumnType(List<CellData> columnCells) {
        if (columnCells.size() < MIN_SAMPLE_SIZE) {
            return "UNKNOWN";
        }

        // Count non-null cells by type
        Map<String, Long> typeCounts = columnCells.stream()
                .filter(cell -> cell.getValue() != null)
                .collect(Collectors.groupingBy(CellData::getCellType, Collectors.counting()));

        if (typeCounts.isEmpty()) {
            return "EMPTY";
        }

        long totalNonNull = typeCounts.values().stream().mapToLong(Long::longValue).sum();

        // Find dominant type
        String dominantType = typeCounts.entrySet().stream()
                .max(Map.Entry.comparingByValue())
                .map(Map.Entry::getKey)
                .orElse("UNKNOWN");

        // Check if dominant type meets confidence threshold
        long dominantCount = typeCounts.getOrDefault(dominantType, 0L);
        double confidence = (double) dominantCount / totalNonNull;

        if (confidence >= TYPE_CONFIDENCE_THRESHOLD) {
            return dominantType;
        } else {
            // Mixed types
            return "MIXED";
        }
    }

    private List<String> detectQualityIssues(List<CellData> cells) {
        List<String> issues = new ArrayList<>();

        // Check for excessive nulls
        long nullCount = cells.stream().filter(c -> c.getValue() == null).count();
        double nullPercentage = (double) nullCount / cells.size() * 100;

        if (nullPercentage > 50) {
            issues.add(String.format("High null percentage: %.1f%%", nullPercentage));
        }

        // Check for errors
        long errorCount = cells.stream().filter(c -> c.getError() != null).count();
        if (errorCount > 0) {
            issues.add(String.format("Contains %d error cells", errorCount));
        }

        // Check for formula errors
        long formulaErrorCount = cells.stream()
                .filter(c -> c.getFormula() != null && c.getValue() != null)
                .filter(c -> c.getValue().toString().startsWith("ERROR:"))
                .count();

        if (formulaErrorCount > 0) {
            issues.add(String.format("Contains %d formula errors", formulaErrorCount));
        }

        // Check for inconsistent column types
        Map<Integer, List<CellData>> byColumn = cells.stream()
                .collect(Collectors.groupingBy(CellData::getColumnIndex));

        for (Map.Entry<Integer, List<CellData>> entry : byColumn.entrySet()) {
            int columnIndex = entry.getKey();
            List<CellData> columnCells = entry.getValue();

            Set<String> uniqueTypes = columnCells.stream()
                    .filter(c -> c.getValue() != null)
                    .map(CellData::getCellType)
                    .collect(Collectors.toSet());

            if (uniqueTypes.size() > 2) {  // More than 2 different types
                issues.add(String.format("Column %d has mixed types: %s", columnIndex, uniqueTypes));
            }
        }

        // Check for suspicious numeric patterns (e.g., all same value)
        for (Map.Entry<Integer, List<CellData>> entry : byColumn.entrySet()) {
            int columnIndex = entry.getKey();
            List<CellData> columnCells = entry.getValue();

            List<Object> numericValues = columnCells.stream()
                    .filter(c -> "NUMERIC".equals(c.getCellType()))
                    .map(CellData::getValue)
                    .filter(Objects::nonNull)
                    .collect(Collectors.toList());

            if (numericValues.size() > 10) {
                Set<Object> uniqueValues = new HashSet<>(numericValues);
                if (uniqueValues.size() == 1) {
                    issues.add(String.format("Column %d: all numeric values are identical", columnIndex));
                }
            }
        }

        return issues;
    }
}
