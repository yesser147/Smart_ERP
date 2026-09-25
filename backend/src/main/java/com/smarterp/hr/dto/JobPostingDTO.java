package com.smarterp.hr.dto;

import com.smarterp.hr.domain.JobPosting;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record JobPostingDTO(
        Long jobId,
        String title,
        Long departmentId,
        String departmentType,
        String businessUnit,
        String divisionDescription,
        String location,
        BigDecimal requiredExperienceYears,
        BigDecimal offeredSalaryMin,
        BigDecimal offeredSalaryMax,
        String status,
        Integer applicantCount,
        String description,
        LocalDateTime createdAt
) {

    public static JobPostingDTO fromEntity(JobPosting p, int applicantCount) {
        var dept = p.getDepartment();
        return new JobPostingDTO(
                p.getJobId(),
                p.getTitle(),
                dept != null ? dept.getDepartmentId() : null,
                dept != null ? dept.getDepartmentType() : null,
                dept != null ? dept.getBusinessUnit() : null,
                dept != null ? dept.getDivisionDescription() : null,
                p.getLocation(),
                p.getRequiredExperienceYears(),
                p.getOfferedSalaryMin(),
                p.getOfferedSalaryMax(),
                p.getStatus(),
                applicantCount,
                p.getDescription(),
                p.getCreatedAt()
        );
    }
}
