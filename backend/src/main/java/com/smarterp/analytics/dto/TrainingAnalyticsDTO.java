package com.smarterp.analytics.dto;

import java.math.BigDecimal;

import com.smarterp.analytics.domain.TrainingAnalytics;

public record TrainingAnalyticsDTO(

    Long departmentId,

    String businessUnit,

    Long trainedEmployeesCount,

    Long totalTrainingsCompleted,

    BigDecimal totalTrainingInvestment,

    BigDecimal avgCourseDurationDays

) {

    public static TrainingAnalyticsDTO fromEntity(
            TrainingAnalytics entity) {

        return new TrainingAnalyticsDTO(
            entity.getDepartmentId(),
            entity.getBusinessUnit(),
            entity.getTrainedEmployeesCount(),
            entity.getTotalTrainingsCompleted(),
            entity.getTotalTrainingInvestment(),
            entity.getAvgCourseDurationDays()
        );
    }
}