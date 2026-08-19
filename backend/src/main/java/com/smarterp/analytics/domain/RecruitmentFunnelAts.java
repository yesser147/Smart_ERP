package com.smarterp.analytics.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

import org.hibernate.annotations.Immutable;

@Entity
@Table(name = "v_recruitment_funnel_ats")
@Immutable
@Getter
@NoArgsConstructor
public class RecruitmentFunnelAts {

    @Id
    @Column(name = "job_id")
    private Long jobId;

    @Column(name = "job_title")
    private String jobTitle;

    @Column(name = "department_id")
    private Long departmentId;

    @Column(name = "posting_status")
    private String postingStatus;

    @Column(name = "offered_salary_min")
    private BigDecimal offeredSalaryMin;

    @Column(name = "offered_salary_max")
    private BigDecimal offeredSalaryMax;

    @Column(name = "total_applications")
    private Long totalApplications;

    @Column(name = "pending_applications")
    private Long pendingApplications;

    @Column(name = "hired_count")
    private Long hiredCount;

    @Column(name = "rejected_count")
    private Long rejectedCount;

    @Column(name = "avg_desired_salary")
    private BigDecimal avgDesiredSalary;

    @Column(name = "avg_ai_match_score")
    private BigDecimal avgAiMatchScore;
}