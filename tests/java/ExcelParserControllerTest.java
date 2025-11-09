package com.customeranalysis.excel.controller;

import com.customeranalysis.excel.dto.ParseRequest;
import com.customeranalysis.excel.dto.ParseResponse;
import com.customeranalysis.excel.service.ExcelParserService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(ExcelParserController.class)
class ExcelParserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ExcelParserService parserService;

    @Test
    void health_ReturnsOk() throws Exception {
        mockMvc.perform(get("/api/v1/excel/health"))
                .andExpect(status().isOk())
                .andExpect(content().string("Java Layer: Excel Parser Service is running"));
    }

    @Test
    void parseExcelFile_Success() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file",
                "test.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "test data".getBytes()
        );

        ParseResponse mockResponse = new ParseResponse();
        when(parserService.parseExcel(any(ParseRequest.class))).thenReturn(mockResponse);

        mockMvc.perform(multipart("/api/v1/excel/parse")
                        .file(file)
                        .param("sheetName", "Sheet1"))
                .andExpect(status().isOk());
    }

    @Test
    void parseExcelFromPath_Success() throws Exception {
        ParseResponse mockResponse = new ParseResponse();
        when(parserService.parseExcel(any(ParseRequest.class))).thenReturn(mockResponse);

        mockMvc.perform(post("/api/v1/excel/parse-from-path")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"filePath\":\"/test/file.xlsx\"}"))
                .andExpect(status().isOk());
    }
}
