package com.customeranalysis.excel;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Main application entry point for Excel POI Parser Service
 * Java layer - handles Excel file parsing using Apache POI
 */
@SpringBootApplication
public class ExcelParserApplication {

    public static void main(String[] args) {
        SpringApplication.run(ExcelParserApplication.class, args);
    }
}
