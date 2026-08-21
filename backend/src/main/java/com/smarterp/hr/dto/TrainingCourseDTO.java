package com.smarterp.hr.dto;

import java.math.BigDecimal;

public record TrainingCourseDTO(

    Long courseId,
    String programName,
    String trainingType,
    String trainer,
    BigDecimal durationDays,
    BigDecimal cost,
    Boolean isActive

) {

    public static TrainingCourseDTO fromEntity(
            com.smarterp.hr.domain.TrainingCourse entity) {

        return new TrainingCourseDTO(
            entity.getCourseId(),
            entity.getProgramName(),
            entity.getTrainingType(),
            entity.getTrainer(),
            entity.getDurationDays(),
            entity.getCost(),
            entity.getIsActive()
        );
    }
}