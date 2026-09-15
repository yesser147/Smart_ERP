package com.smarterp.hr.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record ApplicantWithCvStatusDTO(
    Long applicantId,
    String firstName,
    String lastName,
    String email,
    String educationLevel,
    BigDecimal yearsOfExperience,
    boolean hasCv,
    boolean isProcessed,
    LocalDateTime createdAt
) {}