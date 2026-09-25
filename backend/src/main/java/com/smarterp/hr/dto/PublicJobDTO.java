package com.smarterp.hr.dto;

import com.smarterp.hr.domain.JobPosting;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/** What candidates see on the careers page (no internal data). */
public record PublicJobDTO(Long jobId, String title, String department, String location,
                           BigDecimal requiredExperienceYears, BigDecimal salaryMin, BigDecimal salaryMax,
                           String description, LocalDateTime postedAt) {

    public static PublicJobDTO fromEntity(JobPosting p) {
        return new PublicJobDTO(p.getJobId(), p.getTitle(),
                p.getDepartment() != null ? p.getDepartment().getDepartmentType() : null,
                p.getLocation(), p.getRequiredExperienceYears(), p.getOfferedSalaryMin(),
                p.getOfferedSalaryMax(), p.getDescription(), p.getCreatedAt());
    }
}
