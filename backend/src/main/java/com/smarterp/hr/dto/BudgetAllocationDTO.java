package com.smarterp.hr.dto;

import com.smarterp.hr.domain.DepartmentBudgetAllocation;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record BudgetAllocationDTO(Long id, Long departmentId, String departmentName,
                                  BigDecimal allocatedBudget, BigDecimal predictedPerformance,
                                  String fiscalPeriod, LocalDateTime createdAt) {

    public static BudgetAllocationDTO fromEntity(DepartmentBudgetAllocation a) {
        var d = a.getDepartment();
        String team = d.getDivisionDescription() != null ? d.getDivisionDescription() : d.getBusinessUnit();
        return new BudgetAllocationDTO(a.getId(), d.getDepartmentId(), d.getDepartmentType() + " · " + team,
                a.getAllocatedBudget(), a.getPredictedPerformance(), a.getFiscalPeriod(), a.getCreatedAt());
    }
}
