package com.smarterp.hr.dto;

import com.smarterp.security.domain.RoleName;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;
import java.util.UUID;

public record CreateEmployeeRequest(
    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    String email,

    @NotBlank(message = "Password is required")
    String password,

    @NotNull(message = "Role is required")
    RoleName role,

    UUID departmentId,

    @NotBlank(message = "First name is required")
    String firstName,

    @NotBlank(message = "Last name is required")
    String lastName,

    String phone,

    @NotBlank(message = "Position is required")
    String position,

    @NotNull(message = "Hire date is required")
    LocalDate hireDate
) {}