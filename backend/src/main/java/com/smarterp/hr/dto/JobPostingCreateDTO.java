package com.smarterp.hr.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;

public record JobPostingCreateDTO(
        @NotBlank(message = "Title is required.") @Size(max = 150) String title,
        @NotNull(message = "Team is required.") Long departmentId,
        @Size(max = 100) String location,
        @DecimalMin("0") BigDecimal requiredExperienceYears,
        @DecimalMin("0") BigDecimal offeredSalaryMin,
        @DecimalMin("0") BigDecimal offeredSalaryMax,
        @Size(max = 10000) String description
) {}
