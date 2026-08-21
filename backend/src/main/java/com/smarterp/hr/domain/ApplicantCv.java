package com.smarterp.hr.domain;

import jakarta.persistence.*;
import lombok.*;
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

    @Column(columnDefinition = "jsonb")
    private String extractedSkillsJson;

    @Column(name = "cv_embedding", columnDefinition = "vector(384)")
    private String cvEmbedding; // Standard String representation for pgvector data

    private LocalDateTime createdAt = LocalDateTime.now();
}