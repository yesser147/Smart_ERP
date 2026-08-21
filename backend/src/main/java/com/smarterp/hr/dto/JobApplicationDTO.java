package com.smarterp.hr.dto;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.UUID;

public record JobApplicationDTO(

    UUID applicationId,
    Long applicantId,
    String applicantName,
    Long jobId,
    String jobTitle,
    LocalDate applicationDate,
    BigDecimal desiredSalary,
    String status,
    Integer aiMatchScore

) {

    public static JobApplicationDTO fromEntity(
            com.smarterp.hr.domain.JobApplication entity) {

        String applicantName = null;

        if (entity.getApplicant() != null) {
            applicantName =
                entity.getApplicant().getFirstName()
                + " "
                + entity.getApplicant().getLastName();
        }

        return new JobApplicationDTO(
            entity.getApplicationId(),

            entity.getApplicant() != null
                ? entity.getApplicant().getApplicantId()
                : null,

            applicantName,

            entity.getJobPosting() != null
                ? entity.getJobPosting().getJobId()
                : null,

            entity.getJobPosting() != null
                ? entity.getJobPosting().getTitle()
                : null,

            entity.getApplicationDate(),
            entity.getDesiredSalary(),
            entity.getStatus(),
            entity.getAiMatchScore()
        );
    }
}