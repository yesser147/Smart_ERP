package com.smarterp.analytics.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

import java.math.BigDecimal;

@Entity
@Table(name = "v_department_type_turnover")
@Immutable
public class DepartmentTypeTurnover {

    @Id
    @Column(name = "department_type")
    private String departmentType;

    @Column(name = "total_employees")
    private Long totalEmployees;

    @Column(name = "active_count")
    private Long activeCount;

    @Column(name = "terminated_count")
    private Long terminatedCount;

    @Column(name = "turnover_rate_pct")
    private BigDecimal turnoverRatePct;

    // Default Constructor
    public DepartmentTypeTurnover() {
    }

    // Getters
    public String getDepartmentType() {
        return departmentType;
    }

    public Long getTotalEmployees() {
        return totalEmployees;
    }

    public Long getActiveCount() {
        return activeCount;
    }

    public Long getTerminatedCount() {
        return terminatedCount;
    }

    public BigDecimal getTurnoverRatePct() {
        return turnoverRatePct;
    }
}