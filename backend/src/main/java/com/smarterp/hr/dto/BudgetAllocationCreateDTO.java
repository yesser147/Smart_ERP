package com.smarterp.hr.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;

public record BudgetAllocationCreateDTO(
        @NotNull(message = "Team is required.") Long departmentId,
        @NotNull(message = "Budget is required.") @DecimalMin("0") BigDecimal allocatedBudget,
        BigDecimal predictedPerformance,
        @Size(max = 20) String fiscalPeriod
) {}
