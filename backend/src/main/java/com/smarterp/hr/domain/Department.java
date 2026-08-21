package com.smarterp.hr.domain;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "departments")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor
public class Department {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "department_id")
    private Long departmentId;

    private String businessUnit;
    private String departmentType;
    private String divisionDescription;
    private Boolean isDeleted = false;
    private LocalDateTime createdAt = LocalDateTime.now();
}