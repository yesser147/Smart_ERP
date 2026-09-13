package com.smarterp.hr.dto;

import java.util.UUID;

public record JobApplicationSubmissionDTO(
    Long applicantId,
    UUID applicationId,
    String message
) {}