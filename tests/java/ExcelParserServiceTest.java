package com.customeranalysis.excel.service;

import com.customeranalysis.excel.dto.ParseRequest;
import com.customeranalysis.excel.dto.ParseResponse;
import com.customeranalysis.excel.service.extractor.*;
import org.apache.poi.ss.usermodel.Workbook;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
class ExcelParserServiceTest {

    @Mock
    private WorkbookLoaderService workbookLoader;

    @Mock
    private SheetEnumeratorService sheetEnumerator;

    @Mock
    private CellExtractorService cellExtractor;

    @Mock
    private MetadataExtractorService metadataExtractor;

    @Mock
    private DataNormalizerService dataNormalizer;

    @Mock
    private OutputFormatterService outputFormatter;

    @InjectMocks
    private ExcelParserService excelParserService;

    private ParseRequest request;
    private Workbook mockWorkbook;

    @BeforeEach
    void setUp() {
        request = ParseRequest.builder()
                .filePath("/test/file.xlsx")
                .sheetName("Sheet1")
                .build();
        mockWorkbook = mock(Workbook.class);
    }

    @Test
    void parseExcel_Success() throws Exception {
        when(workbookLoader.loadWorkbook(any())).thenReturn(mockWorkbook);
        when(sheetEnumerator.enumerateSheets(any(), any())).thenReturn(java.util.Collections.emptyList());
        when(cellExtractor.extractCells(any(), any())).thenReturn(java.util.Collections.emptyList());
        when(metadataExtractor.extractMetadata(any(), any())).thenReturn(new java.util.HashMap<>());
        when(dataNormalizer.normalizeAndInferTypes(any())).thenReturn(java.util.Collections.emptyMap());
        when(outputFormatter.formatOutput(any(), any())).thenReturn(new ParseResponse());

        ParseResponse response = excelParserService.parseExcel(request);

        assertNotNull(response);
        verify(workbookLoader, times(1)).loadWorkbook(request);
        verify(mockWorkbook, times(1)).close();
    }

    @Test
    void parseExcel_WorkbookLoaderFails_ThrowsException() {
        when(workbookLoader.loadWorkbook(any())).thenThrow(new RuntimeException("Load failed"));

        assertThrows(RuntimeException.class, () -> excelParserService.parseExcel(request));
    }

    @Test
    void parseExcel_CellExtractorFails_ThrowsException() throws Exception {
        when(workbookLoader.loadWorkbook(any())).thenReturn(mockWorkbook);
        when(sheetEnumerator.enumerateSheets(any(), any())).thenReturn(java.util.Collections.emptyList());
        when(cellExtractor.extractCells(any(), any())).thenThrow(new RuntimeException("Extract failed"));

        assertThrows(RuntimeException.class, () -> excelParserService.parseExcel(request));
    }
}
