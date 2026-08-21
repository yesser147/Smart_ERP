package com.smarterp.hr.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

public record EmployeeDTO(

    Long employeeId,
    Long departmentId,
    String departmentName,
    Long managerId,
    String managerName,
    String firstName,
    String lastName,
    LocalDate startDate,
    LocalDate exitDate,
    String title,
    String employeeStatus,
    String employeeType,
    String employeeClassificationType,
    String terminationType,
    String terminationDescription,
    LocalDate dob,
    String state,
    String jobFunction,
    String gender,
    String location,
    String performanceScore,
    BigDecimal currentEmployeeRating,
    BigDecimal salary,
    String currency,
    Boolean needsReview

) {

    public static EmployeeDTO fromEntity(
            com.smarterp.hr.domain.Employee entity) {

        return new EmployeeDTO(
            entity.getEmployeeId(),

            entity.getDepartment() != null
                ? entity.getDepartment().getDepartmentId()
                : null,

            entity.getDepartment() != null
                ? entity.getDepartment().getBusinessUnit()
                : null,

            entity.getManager() != null
                ? entity.getManager().getEmployeeId()
                : null,

            entity.getManager() != null
                ? entity.getManager().getFirstName() + " "
                    + entity.getManager().getLastName()
                : null,

            entity.getFirstName(),
            entity.getLastName(),
            entity.getStartDate(),
            entity.getExitDate(),
            entity.getTitle(),
            entity.getEmployeeStatus(),
            entity.getEmployeeType(),
            entity.getEmployeeClassificationType(),
            entity.getTerminationType(),
            entity.getTerminationDescription(),
            entity.getDob(),
            entity.getState(),
            entity.getJobFunction(),
            entity.getGender(),
            entity.getLocation(),
            entity.getPerformanceScore(),
            entity.getCurrentEmployeeRating(),
            entity.getSalary(),
            entity.getCurrency(),
            entity.getNeedsReview()
        );
    }
}