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
@Table(name = "v_training_analytics")
@Immutable
@Getter
@NoArgsConstructor
public class TrainingAnalytics {

    @Id
    @Column(name = "department_id")
    private Long departmentId;

    @Column(name = "business_unit")
    private String businessUnit;

    @Column(name = "trained_employees_count")
    private Long trainedEmployeesCount;

    @Column(name = "total_trainings_completed")
    private Long totalTrainingsCompleted;

    @Column(name = "total_training_investment")
    private BigDecimal totalTrainingInvestment;

    @Column(name = "avg_course_duration_days")
    private BigDecimal avgCourseDurationDays;
}