package com.smarterp.hr.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

import java.time.LocalDate;

public record LeaveRequestCreateDTO(
        @NotNull(message = "Leave type is required.")
        @Pattern(regexp = "ANNUAL|SICK|UNPAID|OTHER", message = "Unknown leave type.") String leaveType,
        @NotNull(message = "Start date is required.") LocalDate startDate,
        @NotNull(message = "End date is required.") LocalDate endDate,
        @Size(max = 1000) String reason
) {}
