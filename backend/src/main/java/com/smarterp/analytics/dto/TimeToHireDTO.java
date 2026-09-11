package com.smarterp.analytics.dto;

public record TimeToHireDTO(
    Long jobId,
    String jobTitle,
    Long departmentId,
    Double avgDaysToHire,
    Long hiredCount
) {}