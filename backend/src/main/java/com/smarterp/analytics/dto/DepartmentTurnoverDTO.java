package com.smarterp.analytics.dto;

import java.math.BigDecimal;

public record DepartmentTurnoverDTO(
    Long departmentId,
    String businessUnit,
    Long totalEmployees,
    Long activeCount,
    Long terminatedCount,
    BigDecimal turnoverRatePct
) {
    // Static helper method to map Entity to DTO easily
    public static DepartmentTurnoverDTO fromEntity(com.smarterp.analytics.domain.DepartmentTurnoverView entity) {
        return new DepartmentTurnoverDTO(
            entity.getDepartmentId(),
            entity.getBusinessUnit(),
            entity.getTotalEmployees(),
            entity.getActiveCount(),
            entity.getTerminatedCount(),
            entity.getTurnoverRatePct()
        );
    }
}