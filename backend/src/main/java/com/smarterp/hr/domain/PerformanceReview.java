package com.smarterp.hr.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "performance_reviews")
@Getter @Setter @NoArgsConstructor
public class PerformanceReview {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "employee_id", nullable = false)
    private Employee employee;

    private String reviewer;
    private LocalDate reviewDate;
    private Integer rating;

    @Column(columnDefinition = "TEXT")
    private String comments;

    private LocalDateTime createdAt = LocalDateTime.now();
}
