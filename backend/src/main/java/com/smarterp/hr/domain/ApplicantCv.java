package com.smarterp.hr.domain;

import jakarta.persistence.*;
import lombok.*;

import org.hibernate.annotations.Array;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "applicant_cvs")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor
public class ApplicantCv {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "applicant_id", unique = true)
    private Applicant applicant;

    private String fileUrl;

    @Column(columnDefinition = "TEXT")
    private String parsedText;

    @Column(name = "extracted_skills_json")
    @JdbcTypeCode(SqlTypes.JSON)
    private String extractedSkillsJson;
 
    @Column(name = "cv_embedding")
    @JdbcTypeCode(SqlTypes.VECTOR)
    @Array(length = 384)   // must match vector(384) in schema.sql
    private float[] cvEmbedding;

    private LocalDateTime createdAt = LocalDateTime.now();
}