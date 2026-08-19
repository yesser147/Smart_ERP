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
@Table(name = "v_employee_performance_engagement")
@Immutable
@Getter
@NoArgsConstructor
public class EmployeePerformanceEngagement {

    @Id
    @Column(name = "employee_id")
    private Long employeeId;

    @Column(name = "department_id")
    private Long departmentId;

    @Column(name = "job_function")
    private String jobFunction;

    @Column(name = "title")
    private String title;

    @Column(name = "performance_score")
    private String performanceScore;

    @Column(name = "avg_engagement_score")
    private BigDecimal avgEngagementScore;

    @Column(name = "avg_satisfaction_score")
    private BigDecimal avgSatisfactionScore;

    @Column(name = "avg_work_life_balance")
    private BigDecimal avgWorkLifeBalance;
}