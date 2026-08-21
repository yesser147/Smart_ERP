package com.smarterp.hr.domain;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "employees")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor
public class Employee {

    @Id
    @Column(name = "employee_id")
    private Long employeeId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "department_id")
    private Department department;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "manager_id")
    private Employee manager;

    private String firstName;
    private String lastName;
    private LocalDate startDate;
    private LocalDate exitDate;
    private String title;
    private String employeeStatus;
    private String employeeType;
    private String employeeClassificationType;
    private String terminationType;
    
    @Column(columnDefinition = "TEXT")
    private String terminationDescription;
    
    private LocalDate dob;
    private String state;
    private String jobFunction;
    private String gender;
    private String location;
    private String performanceScore;
    private BigDecimal currentEmployeeRating;
    private BigDecimal salary;
    private String currency = "USD";
    private Boolean needsReview = false;
    private Boolean isDeleted = false;

    private LocalDateTime createdAt = LocalDateTime.now();
    private LocalDateTime updatedAt = LocalDateTime.now();
}