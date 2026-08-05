package com.smarterp.hr.dto;

import com.smarterp.hr.domain.EmployeeStatus;
import java.time.LocalDate;
import java.util.UUID;

public record EmployeeDTO(
    UUID id,
    UUID userId,
    String email,
    UUID departmentId,
    String departmentName,
    String firstName,
    String lastName,
    String phone,
    String position,
    LocalDate hireDate,
    EmployeeStatus status
) {}