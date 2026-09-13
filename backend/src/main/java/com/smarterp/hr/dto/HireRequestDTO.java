package com.smarterp.hr.dto;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.UUID;

public record HireRequestDTO(
    Long departmentId,
    String title,
    String employeeType,
    String employeeClassificationType,
    String jobFunction,
    String state,
    String location,
    LocalDate startDate,
    BigDecimal salary,
    String roleName,
    UUID jobApplicationId
) {}