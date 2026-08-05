package com.smarterp.hr.dto;

import com.smarterp.hr.domain.LeaveType;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;
import java.util.UUID;

public record CreateLeaveRequest(
    @NotNull(message = "Employee ID is required")
    UUID employeeId,

    @NotNull(message = "Leave type is required")
    LeaveType leaveType,

    @NotNull(message = "Start date is required")
    LocalDate startDate,

    @NotNull(message = "End date is required")
    LocalDate endDate,

    String reason
) {}