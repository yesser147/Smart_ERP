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
    @GeneratedValue(strategy = GenerationType.IDENTITY)
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

    // Detailed attributes from the IBM HR data set (migration V3); null for
    // people hired through the app until HR fills them in.
    private Integer jobLevel;
    private Boolean overtime;
    private String businessTravel;
    private Integer distanceFromHome;
    private String educationLevel;
    private String educationField;
    private Integer totalWorkingYears;
    private Integer numCompaniesWorked;
    private Integer yearsInCurrentRole;
    private Integer yearsSinceLastPromotion;
    private Integer yearsWithCurrManager;
    private Integer stockOptionLevel;
    private Integer percentSalaryHike;
    private Integer environmentSatisfaction;
    private Integer relationshipSatisfaction;
    private Integer trainingTimesLastYear;
    private Boolean isDeleted = false;

    private LocalDateTime createdAt = LocalDateTime.now();
    private LocalDateTime updatedAt = LocalDateTime.now();
}