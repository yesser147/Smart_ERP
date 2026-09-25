package com.smarterp.shared.audit;

import java.time.LocalDateTime;

public record AuditLogDTO(Long id, String actor, String action, String entityType,
                          String entityId, String details, LocalDateTime createdAt) {

    public static AuditLogDTO fromEntity(AuditLog a) {
        return new AuditLogDTO(a.getId(), a.getActor(), a.getAction(), a.getEntityType(),
                a.getEntityId(), a.getDetails(), a.getCreatedAt());
    }
}
