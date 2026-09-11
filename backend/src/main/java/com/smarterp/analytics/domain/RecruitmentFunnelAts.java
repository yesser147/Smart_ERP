package com.smarterp.analytics.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;
import org.hibernate.annotations.Subselect;

import java.math.BigDecimal;

@Entity
@Immutable
@Table(name = "v_recruitment_funnel_ats")
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

    @Column(name = "applied_count")
    private Long appliedCount;

    @Column(name = "in_review_count")
    private Long inReviewCount;

    @Column(name = "interviewing_count")
    private Long interviewingCount;

    @Column(name = "offered_count")
    private Long offeredCount;

    @Column(name = "rejected_count")
    private Long rejectedCount;

    @Column(name = "avg_desired_salary")
    private BigDecimal avgDesiredSalary;

    @Column(name = "avg_ai_match_score")
    private BigDecimal avgAiMatchScore;

    protected RecruitmentFunnelAts() {
        // JPA needs a no-arg constructor
    }

    public Long getJobId() { return jobId; }
    public String getJobTitle() { return jobTitle; }
    public Long getDepartmentId() { return departmentId; }
    public String getPostingStatus() { return postingStatus; }
    public BigDecimal getOfferedSalaryMin() { return offeredSalaryMin; }
    public BigDecimal getOfferedSalaryMax() { return offeredSalaryMax; }
    public Long getTotalApplications() { return totalApplications; }
    public Long getAppliedCount() { return appliedCount; }
    public Long getInReviewCount() { return inReviewCount; }
    public Long getInterviewingCount() { return interviewingCount; }
    public Long getOfferedCount() { return offeredCount; }
    public Long getRejectedCount() { return rejectedCount; }
    public BigDecimal getAvgDesiredSalary() { return avgDesiredSalary; }
    public BigDecimal getAvgAiMatchScore() { return avgAiMatchScore; }
}