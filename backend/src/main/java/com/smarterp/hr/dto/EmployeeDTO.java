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
    Boolean needsReview,
    Integer jobLevel,
    Boolean overtime,
    String businessTravel,
    Integer distanceFromHome,
    String educationLevel,
    String educationField,
    Integer totalWorkingYears,
    Integer numCompaniesWorked,
    Integer yearsInCurrentRole,
    Integer yearsSinceLastPromotion,
    Integer yearsWithCurrManager,
    Integer stockOptionLevel,
    Integer percentSalaryHike,
    Integer trainingTimesLastYear

) {

    public static EmployeeDTO fromEntity(
            com.smarterp.hr.domain.Employee entity) {

        return new EmployeeDTO(
            entity.getEmployeeId(),

            entity.getDepartment() != null
                ? entity.getDepartment().getDepartmentId()
                : null,

            entity.getDepartment() != null
                ? departmentLabel(entity.getDepartment())
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
            entity.getNeedsReview(),
            entity.getJobLevel(),
            entity.getOvertime(),
            entity.getBusinessTravel(),
            entity.getDistanceFromHome(),
            entity.getEducationLevel(),
            entity.getEducationField(),
            entity.getTotalWorkingYears(),
            entity.getNumCompaniesWorked(),
            entity.getYearsInCurrentRole(),
            entity.getYearsSinceLastPromotion(),
            entity.getYearsWithCurrManager(),
            entity.getStockOptionLevel(),
            entity.getPercentSalaryHike(),
            entity.getTrainingTimesLastYear()
        );
    }

    /** "Sales · Sales Executives - Team 2" (department + team) instead of the team code. */
    private static String departmentLabel(com.smarterp.hr.domain.Department d) {
        String type = d.getDepartmentType();
        String team = d.getDivisionDescription() != null ? d.getDivisionDescription() : d.getBusinessUnit();
        return type != null ? type + " · " + team : team;
    }
}