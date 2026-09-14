package com.smarterp.hr.dto;

public record ApplicantCvStatusView(
        Long applicantId,
        boolean hasCv,
        boolean isProcessed
) {}