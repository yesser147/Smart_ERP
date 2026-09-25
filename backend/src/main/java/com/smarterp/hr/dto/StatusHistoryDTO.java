package com.smarterp.hr.dto;

import com.smarterp.hr.domain.ApplicationStatusHistory;

import java.time.LocalDateTime;

public record StatusHistoryDTO(String oldStatus, String newStatus, String changedBy, LocalDateTime changedAt) {

    public static StatusHistoryDTO fromEntity(ApplicationStatusHistory h) {
        return new StatusHistoryDTO(h.getOldStatus(), h.getNewStatus(), h.getChangedBy(), h.getChangedAt());
    }
}
