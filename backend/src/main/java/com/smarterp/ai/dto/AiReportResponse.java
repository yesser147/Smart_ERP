package com.smarterp.ai.dto;

import java.util.List;

public record AiReportResponse(
    String summary,
    List<String> insights,
    Long executionTimeMs
) {}