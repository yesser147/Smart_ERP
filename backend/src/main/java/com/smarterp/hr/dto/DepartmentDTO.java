package com.smarterp.hr.dto;

public record DepartmentDTO(

    Long departmentId,
    String businessUnit,
    String departmentType,
    String divisionDescription

) {

    public static DepartmentDTO fromEntity(
            com.smarterp.hr.domain.Department entity) {

        return new DepartmentDTO(
            entity.getDepartmentId(),
            entity.getBusinessUnit(),
            entity.getDepartmentType(),
            entity.getDivisionDescription()
        );
    }
}