package com.smarterp.hr.domain;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;

@Entity
@Table(name = "training_courses")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor
public class TrainingCourse {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "course_id")
    private Long courseId;

    @Column(unique = true, nullable = false)
    private String programName;
    private String trainingType;
    private String trainer;
    private BigDecimal durationDays;
    private BigDecimal cost;
    private Boolean isActive = true;
}