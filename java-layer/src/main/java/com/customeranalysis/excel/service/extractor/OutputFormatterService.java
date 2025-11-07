package com.customeranalysis.excel.service.extractor;

import com.customeranalysis.excel.dto.ParseResponse;
import com.customeranalysis.excel.model.NormalizedData;
import com.customeranalysis.excel.model.WorkbookMetadata;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

/**
 * Output Formatter
 * Formats data as JSON for consumption by Python aggregation layer
 */
@Service
@Slf4j
public class OutputFormatterService {

    public ParseResponse formatOutput(NormalizedData data, WorkbookMetadata metadata) {
        log.debug("Formatting output");

        ParseResponse response = new ParseResponse();
        response.setSuccess(true);
        response.setMetadata(metadata);
        response.setData(data);
        response.setTimestamp(System.currentTimeMillis());

        log.info("Formatted output with {} cells", data.getTotalCells());
        return response;
    }
}
