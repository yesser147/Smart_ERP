package com.smarterp.hr.dto;

import java.util.UUID;

public record ApplicantCvDTO(

    UUID id,
    Long applicantId,
    String fileUrl,
    String parsedText,
    String extractedSkillsJson

) {

    public static ApplicantCvDTO fromEntity(
            com.smarterp.hr.domain.ApplicantCv entity) {

        return new ApplicantCvDTO(
            entity.getId(),

            entity.getApplicant() != null
                ? entity.getApplicant().getApplicantId()
                : null,

            entity.getFileUrl(),
            entity.getParsedText(),
            entity.getExtractedSkillsJson()
        );
    }
}