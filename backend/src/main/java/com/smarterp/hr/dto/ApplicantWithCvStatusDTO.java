package com.smarterp.hr.dto;

public record ApplicantWithCvStatusDTO(
    Long applicantId,
    String firstName,
    String lastName,
    String email,
    String educationLevel,
    java.math.BigDecimal yearsOfExperience,
    boolean hasCv,
    boolean isProcessed
) {}