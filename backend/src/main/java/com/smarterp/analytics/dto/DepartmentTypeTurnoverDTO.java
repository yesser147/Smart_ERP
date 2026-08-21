package com.smarterp.analytics.dto;

import java.math.BigDecimal;

public record DepartmentTypeTurnoverDTO(

    String departmentType,
    Long totalEmployees,
    Long activeCount,
    Long terminatedCount,
    BigDecimal turnoverRatePct

) {

    public static DepartmentTypeTurnoverDTO fromEntity(
            com.smarterp.analytics.domain.DepartmentTypeTurnover entity) {

        return new DepartmentTypeTurnoverDTO(
            entity.getDepartmentType(),
            entity.getTotalEmployees(),
            entity.getActiveCount(),
            entity.getTerminatedCount(),
            entity.getTurnoverRatePct()
        );
    }
}