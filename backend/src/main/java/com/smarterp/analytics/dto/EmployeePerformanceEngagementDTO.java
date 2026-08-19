package com.smarterp.analytics.dto;

import java.math.BigDecimal;

import com.smarterp.analytics.domain.EmployeePerformanceEngagement;

public record EmployeePerformanceEngagementDTO(

    Long employeeId,

    Long departmentId,

    String jobFunction,

    String title,

    String performanceScore,

    BigDecimal avgEngagementScore,

    BigDecimal avgSatisfactionScore,

    BigDecimal avgWorkLifeBalance

) {

    public static EmployeePerformanceEngagementDTO fromEntity(
            EmployeePerformanceEngagement entity) {

        return new EmployeePerformanceEngagementDTO(
            entity.getEmployeeId(),
            entity.getDepartmentId(),
            entity.getJobFunction(),
            entity.getTitle(),
            entity.getPerformanceScore(),
            entity.getAvgEngagementScore(),
            entity.getAvgSatisfactionScore(),
            entity.getAvgWorkLifeBalance()
        );
    }
}