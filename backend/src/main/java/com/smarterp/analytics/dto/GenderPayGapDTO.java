package com.smarterp.analytics.dto;

public record GenderPayGapDTO(
    String businessUnit,
    String gender,
    Double avgSalary,
    Long employeeCount
) {}