package com.smarterp.hr.dto;

import com.smarterp.hr.domain.AttendanceStatus;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.UUID;

public record AttendanceDTO(
    UUID id,
    UUID employeeId,
    String employeeName,
    LocalDate workDate,
    LocalTime checkIn,
    LocalTime checkOut,
    AttendanceStatus status
) {}