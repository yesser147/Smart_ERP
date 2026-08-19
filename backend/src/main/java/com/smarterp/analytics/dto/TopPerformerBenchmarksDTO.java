package com.smarterp.analytics.dto;

import java.math.BigDecimal;

import com.smarterp.analytics.domain.TopPerformerBenchmarks;

public record TopPerformerBenchmarksDTO(

    Long employeeId,

    Long departmentId,

    String jobFunction,

    String title,

    String performanceScore,

    String gender,

    BigDecimal avgEngagement

) {

    public static TopPerformerBenchmarksDTO fromEntity(
            TopPerformerBenchmarks entity) {

        return new TopPerformerBenchmarksDTO(
            entity.getEmployeeId(),
            entity.getDepartmentId(),
            entity.getJobFunction(),
            entity.getTitle(),
            entity.getPerformanceScore(),
            entity.getGender(),
            entity.getAvgEngagement()
        );
    }
}