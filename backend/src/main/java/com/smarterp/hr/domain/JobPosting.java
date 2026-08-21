package com.smarterp.hr.domain;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "job_postings")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor
public class JobPosting {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "job_id")
    private Long jobId;

    @Column(nullable = false)
    private String title;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "department_id")
    private Department department;

    private String location;
    private BigDecimal requiredExperienceYears;
    private BigDecimal offeredSalaryMin;
    private BigDecimal offeredSalaryMax;
    private String status = "OPEN";
    private LocalDateTime createdAt = LocalDateTime.now();
}