package com.smarterp.hr.domain;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "salary_history")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor
public class SalaryHistory {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "employee_id", nullable = false)
    private Employee employee;

    private LocalDate effectiveDate;
    private BigDecimal salary;
    private String currency = "USD";
    private String changeReason;
    private LocalDateTime createdAt = LocalDateTime.now();
}