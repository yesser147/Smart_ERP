package com.smarterp.hr.domain;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@Table(name = "engagement_surveys")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor
public class EngagementSurvey {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "employee_id")
    private Employee employee;

    private LocalDate surveyDate;
    private BigDecimal engagementScore;
    private BigDecimal satisfactionScore;
    private BigDecimal workLifeBalanceScore;
}