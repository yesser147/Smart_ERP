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
@Table(name = "v_department_turnover")
@Immutable 
@Getter
@NoArgsConstructor
public class DepartmentTurnoverView {

    @Id
    @Column(name = "department_id")
    private Long departmentId;

    @Column(name = "business_unit")
    private String businessUnit;

    @Column(name = "total_employees")
    private Long totalEmployees;

    @Column(name = "active_count")
    private Long activeCount;

    @Column(name = "terminated_count")
    private Long terminatedCount;

    @Column(name = "turnover_rate_pct")
    private BigDecimal turnoverRatePct;
}