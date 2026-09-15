package com.smarterp.hr.domain;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "applicants")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor
public class Applicant {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "applicant_id")
    private Long applicantId;

    private String firstName;
    private String lastName;

    @Column(nullable = false, unique = true)
    private String email;
    private String phoneNumber;
    private String educationLevel;
    private BigDecimal yearsOfExperience;
    private String gender;
    private LocalDate dob;

    @Column(columnDefinition = "TEXT")
    private String address;

    private String city;
    private String state;
    private String zipCode;
    private String country;
    private LocalDateTime createdAt = LocalDateTime.now();
}