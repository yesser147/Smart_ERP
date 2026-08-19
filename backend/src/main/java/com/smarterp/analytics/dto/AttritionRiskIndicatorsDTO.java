package com.smarterp.analytics.dto;

import com.smarterp.analytics.domain.AttritionRiskIndicators;

import java.math.BigDecimal;
import java.time.LocalDate;

public record AttritionRiskIndicatorsDTO(

    Long employeeId,

    Long departmentId,

    String jobFunction,

    String title,

    String performanceScore,

    BigDecimal salary,

    LocalDate startDate,

    BigDecimal recentEngagement,

    BigDecimal recentSatisfaction,

    BigDecimal recentWlb,

    String heuristicRiskLevel

) {

    public static AttritionRiskIndicatorsDTO fromEntity(
            AttritionRiskIndicators entity) {

        return new AttritionRiskIndicatorsDTO(
            entity.getEmployeeId(),
            entity.getDepartmentId(),
            entity.getJobFunction(),
            entity.getTitle(),
            entity.getPerformanceScore(),
            entity.getSalary(),
            entity.getStartDate(),
            entity.getRecentEngagement(),
            entity.getRecentSatisfaction(),
            entity.getRecentWlb(),
            entity.getHeuristicRiskLevel()
        );
    }
}