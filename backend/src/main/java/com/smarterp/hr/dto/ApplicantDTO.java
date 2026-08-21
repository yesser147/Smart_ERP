package com.smarterp.hr.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

public record ApplicantDTO(

    Long applicantId,
    String firstName,
    String lastName,
    String email,
    String phoneNumber,
    String educationLevel,
    BigDecimal yearsOfExperience,
    String gender,
    LocalDate dob,
    String address,
    String city,
    String state,
    String zipCode,
    String country

) {

    public static ApplicantDTO fromEntity(
            com.smarterp.hr.domain.Applicant entity) {

        return new ApplicantDTO(
            entity.getApplicantId(),
            entity.getFirstName(),
            entity.getLastName(),
            entity.getEmail(),
            entity.getPhoneNumber(),
            entity.getEducationLevel(),
            entity.getYearsOfExperience(),
            entity.getGender(),
            entity.getDob(),
            entity.getAddress(),
            entity.getCity(),
            entity.getState(),
            entity.getZipCode(),
            entity.getCountry()
        );
    }
}