package com.smarterp.hr.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "application_status_history")
@Getter @Setter @NoArgsConstructor
public class ApplicationStatusHistory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "application_id", nullable = false)
    private UUID applicationId;

    private String oldStatus;
    private String newStatus;
    private String changedBy;
    private LocalDateTime changedAt = LocalDateTime.now();

    public ApplicationStatusHistory(UUID applicationId, String oldStatus, String newStatus, String changedBy) {
        this.applicationId = applicationId;
        this.oldStatus = oldStatus;
        this.newStatus = newStatus;
        this.changedBy = changedBy;
    }
}
