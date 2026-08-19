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
@Table(name = "v_top_performer_benchmarks")
@Immutable
@Getter
@NoArgsConstructor
public class TopPerformerBenchmarks {

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

    @Column(name = "gender")
    private String gender;

    @Column(name = "avg_engagement")
    private BigDecimal avgEngagement;
}