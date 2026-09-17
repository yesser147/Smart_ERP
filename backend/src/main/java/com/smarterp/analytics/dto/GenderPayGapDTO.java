package com.smarterp.analytics.dto;

public record GenderPayGapDTO(
    String departmentType,
    String divisionDescription,
    String gender,
    Double avgSalary,
    Long employeeCount
) {}