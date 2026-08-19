package com.smarterp.analytics.dto;

import java.math.BigDecimal;

import com.smarterp.analytics.domain.RecruitmentFunnelAts;

public record RecruitmentFunnelAtsDTO(

    Long jobId,

    String jobTitle,

    Long departmentId,

    String postingStatus,

    BigDecimal offeredSalaryMin,

    BigDecimal offeredSalaryMax,

    Long totalApplications,

    Long pendingApplications,

    Long hiredCount,

    Long rejectedCount,

    BigDecimal avgDesiredSalary,

    BigDecimal avgAiMatchScore

) {

    public static RecruitmentFunnelAtsDTO fromEntity(
            RecruitmentFunnelAts entity) {

        return new RecruitmentFunnelAtsDTO(
            entity.getJobId(),
            entity.getJobTitle(),
            entity.getDepartmentId(),
            entity.getPostingStatus(),
            entity.getOfferedSalaryMin(),
            entity.getOfferedSalaryMax(),
            entity.getTotalApplications(),
            entity.getPendingApplications(),
            entity.getHiredCount(),
            entity.getRejectedCount(),
            entity.getAvgDesiredSalary(),
            entity.getAvgAiMatchScore()
        );
    }
}