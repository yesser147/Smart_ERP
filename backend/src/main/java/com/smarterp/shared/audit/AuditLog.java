package com.smarterp.shared.audit;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Entity
@Table(name = "audit_log")
@Getter @Setter @NoArgsConstructor
public class AuditLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String actor;
    private String action;
    private String entityType;
    private String entityId;

    @Column(columnDefinition = "TEXT")
    private String details;

    private LocalDateTime createdAt = LocalDateTime.now();
}
