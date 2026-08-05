package com.smarterp.hr.dto;

import com.smarterp.hr.domain.LeaveStatus;
import com.smarterp.hr.domain.LeaveType;
import java.time.LocalDate;
import java.util.UUID;

public record LeaveRequestDTO(
    UUID id,
    UUID employeeId,
    String employeeName,
    LeaveType leaveType,
    LocalDate startDate,
    LocalDate endDate,
    LeaveStatus status,
    String reason,
    UUID approvedById
) {}