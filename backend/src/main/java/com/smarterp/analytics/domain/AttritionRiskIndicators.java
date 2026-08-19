package com.smarterp.analytics.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Immutable;

import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@Table(name = "v_attrition_risk_indicators")
@Immutable
@Getter
@NoArgsConstructor
public class AttritionRiskIndicators {

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

    @Column(name = "salary")
    private BigDecimal salary;

    @Column(name = "start_date")
    private LocalDate startDate;

    @Column(name = "recent_engagement")
    private BigDecimal recentEngagement;

    @Column(name = "recent_satisfaction")
    private BigDecimal recentSatisfaction;

    @Column(name = "recent_wlb")
    private BigDecimal recentWlb;

    @Column(name = "heuristic_risk_level")
    private String heuristicRiskLevel;
}