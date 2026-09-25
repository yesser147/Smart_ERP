package com.smarterp.hr.dto;

import com.smarterp.hr.domain.LeaveRequest;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

public record LeaveRequestDTO(Long id, Long employeeId, String employeeName, String leaveType,
                              LocalDate startDate, LocalDate endDate, long days, String reason,
                              String status, String decidedBy, LocalDateTime decidedAt,
                              LocalDateTime createdAt) {

    public static LeaveRequestDTO fromEntity(LeaveRequest l) {
        var e = l.getEmployee();
        return new LeaveRequestDTO(l.getId(), e.getEmployeeId(), e.getFirstName() + " " + e.getLastName(),
                l.getLeaveType(), l.getStartDate(), l.getEndDate(),
                ChronoUnit.DAYS.between(l.getStartDate(), l.getEndDate()) + 1,
                l.getReason(), l.getStatus(), l.getDecidedBy(), l.getDecidedAt(), l.getCreatedAt());
    }
}
