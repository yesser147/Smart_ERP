package com.smarterp.hr.dto;

import java.math.BigDecimal;

public record JobPostingDTO(

    Long jobId,
    String title,
    Long departmentId,
    String departmentName,
    String location,
    BigDecimal requiredExperienceYears,
    BigDecimal offeredSalaryMin,
    BigDecimal offeredSalaryMax,
    String status

) {

    public static JobPostingDTO fromEntity(
            com.smarterp.hr.domain.JobPosting entity) {

        return new JobPostingDTO(
            entity.getJobId(),
            entity.getTitle(),

            entity.getDepartment() != null
                ? entity.getDepartment().getDepartmentId()
                : null,

            entity.getDepartment() != null
                ? entity.getDepartment().getBusinessUnit()
                : null,

            entity.getLocation(),
            entity.getRequiredExperienceYears(),
            entity.getOfferedSalaryMin(),
            entity.getOfferedSalaryMax(),
            entity.getStatus()
        );
    }
}