package com.smarterp.analytics.domain;

import jakarta.persistence.Column;
import jakarta.persistence.EmbeddedId;
import jakarta.persistence.Entity;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

import org.hibernate.annotations.Immutable;

@Entity
@Table(name = "v_salary_distribution")
@Immutable
@Getter
@NoArgsConstructor
public class SalaryDistribution {

    @EmbeddedId
    private SalaryDistributionId id;

    @Column(name = "business_unit")
    private String businessUnit;

    @Column(name = "employee_count")
    private Long employeeCount;

    @Column(name = "avg_salary")
    private BigDecimal avgSalary;

    @Column(name = "min_salary")
    private BigDecimal minSalary;

    @Column(name = "max_salary")
    private BigDecimal maxSalary;

    @Column(name = "total_payroll_burden")
    private BigDecimal totalPayrollBurden;
}