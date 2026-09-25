package com.smarterp.hr.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "department_budget_allocations")
@Getter @Setter @NoArgsConstructor
public class DepartmentBudgetAllocation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "department_id", nullable = false)
    private Department department;

    private BigDecimal allocatedBudget;
    private BigDecimal predictedPerformance;

    @Column(name = "approved_by")
    private UUID approvedBy;

    private String fiscalPeriod;
    private LocalDateTime createdAt = LocalDateTime.now();
}
