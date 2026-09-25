package com.smarterp.shared.notification;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "notifications")
@Getter @Setter @NoArgsConstructor
public class Notification {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    private String title;

    @Column(columnDefinition = "TEXT")
    private String message;

    private String link;
    private Boolean isRead = false;
    private LocalDateTime createdAt = LocalDateTime.now();
}
