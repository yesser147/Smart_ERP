package com.smarterp.admin;

import com.smarterp.hr.domain.Department;
import com.smarterp.hr.domain.Employee;

/** An employee who can receive an account (no login yet). */
public record EmployeeOptionDTO(Long employeeId, String name, String title, String team) {

    public static EmployeeOptionDTO fromEntity(Employee e) {
        Department d = e.getDepartment();
        String team = d == null ? null : d.getDivisionDescription() != null ? d.getDivisionDescription() : d.getBusinessUnit();
        return new EmployeeOptionDTO(e.getEmployeeId(), e.getFirstName() + " " + e.getLastName(), e.getTitle(), team);
    }
}
