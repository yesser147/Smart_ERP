package com.smarterp.shared.notification;

import java.time.LocalDateTime;

public record NotificationDTO(Long id, String title, String message, String link,
                              boolean read, LocalDateTime createdAt) {

    public static NotificationDTO fromEntity(Notification n) {
        return new NotificationDTO(n.getId(), n.getTitle(), n.getMessage(), n.getLink(),
                Boolean.TRUE.equals(n.getIsRead()), n.getCreatedAt());
    }
}
