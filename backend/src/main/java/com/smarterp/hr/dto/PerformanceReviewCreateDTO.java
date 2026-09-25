package com.smarterp.hr.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record PerformanceReviewCreateDTO(
        @NotNull(message = "Rating is required.") @Min(1) @Max(5) Integer rating,
        @Size(max = 2000) String comments
) {}
