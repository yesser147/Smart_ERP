package com.smarterp.hr.dto;

import java.time.LocalDate;

public record EmployeeTrainingDTO(

    Long id,
    Long employeeId,
    String employeeName,
    Long courseId,
    String programName,
    LocalDate trainingDate,
    String completionStatus,
    String location

) {

    public static EmployeeTrainingDTO fromEntity(
            com.smarterp.hr.domain.EmployeeTraining entity) {

        String employeeName = null;

        if (entity.getEmployee() != null) {
            employeeName =
                entity.getEmployee().getFirstName()
                + " "
                + entity.getEmployee().getLastName();
        }

        return new EmployeeTrainingDTO(
            entity.getId(),

            entity.getEmployee() != null
                ? entity.getEmployee().getEmployeeId()
                : null,

            employeeName,

            entity.getCourse() != null
                ? entity.getCourse().getCourseId()
                : null,

            entity.getCourse() != null
                ? entity.getCourse().getProgramName()
                : null,

            entity.getTrainingDate(),
            entity.getCompletionStatus(),
            entity.getLocation()
        );
    }
}