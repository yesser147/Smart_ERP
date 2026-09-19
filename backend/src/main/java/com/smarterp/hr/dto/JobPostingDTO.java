package com.smarterp.hr.dto;

import lombok.Getter;
import java.math.BigDecimal;

@Getter
public class JobPostingDTO {
    private Long jobId;
    private String title;
    private Long departmentId;
    private String departmentType;
    private String businessUnit;
    private String divisionDescription;
    private String location;
    private BigDecimal requiredExperienceYears;
    private BigDecimal offeredSalaryMin;
    private BigDecimal offeredSalaryMax;
    private String status;
    private Integer applicantCount;

    public JobPostingDTO(Long jobId, String title, Long departmentId,
                          String departmentType, String businessUnit,
                          String divisionDescription, String location,
                          BigDecimal requiredExperienceYears,
                          BigDecimal offeredSalaryMin, BigDecimal offeredSalaryMax,
                          String status) {
        this.jobId = jobId;
        this.title = title;
        this.departmentId = departmentId;
        this.departmentType = departmentType;
        this.businessUnit = businessUnit;
        this.divisionDescription = divisionDescription;
        this.location = location;
        this.requiredExperienceYears = requiredExperienceYears;
        this.offeredSalaryMin = offeredSalaryMin;
        this.offeredSalaryMax = offeredSalaryMax;
        this.status = status;
    }

    public static JobPostingDTO fromEntity(com.smarterp.hr.domain.JobPosting entity) {
        var dept = entity.getDepartment();

        return new JobPostingDTO(
            entity.getJobId(),
            entity.getTitle(),
            dept != null ? dept.getDepartmentId() : null,
            dept != null ? dept.getDepartmentType() : null,
            dept != null ? dept.getBusinessUnit() : null,
            dept != null ? dept.getDivisionDescription() : null,
            entity.getLocation(),
            entity.getRequiredExperienceYears(),
            entity.getOfferedSalaryMin(),
            entity.getOfferedSalaryMax(),
            entity.getStatus()
        );
    }
}