package com.smarterp.hr.dto;

public record HireResultDTO(
    Long employeeId,
    String email,
    boolean activationEmailSent
) {}