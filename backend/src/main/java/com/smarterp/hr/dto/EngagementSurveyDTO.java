package com.smarterp.hr.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

public record EngagementSurveyDTO(

    Long id,
    Long employeeId,
    LocalDate surveyDate,
    BigDecimal engagementScore,
    BigDecimal satisfactionScore,
    BigDecimal workLifeBalanceScore

) {

    public static EngagementSurveyDTO fromEntity(
            com.smarterp.hr.domain.EngagementSurvey entity) {

        return new EngagementSurveyDTO(
            entity.getId(),

            entity.getEmployee() != null
                ? entity.getEmployee().getEmployeeId()
                : null,

            entity.getSurveyDate(),
            entity.getEngagementScore(),
            entity.getSatisfactionScore(),
            entity.getWorkLifeBalanceScore()
        );
    }
}