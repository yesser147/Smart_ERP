package com.smarterp.hr.repository;

import com.smarterp.hr.domain.Employee;
import com.smarterp.hr.domain.EmployeeStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface EmployeeRepository extends JpaRepository<Employee, UUID> {
    Optional<Employee> findByUserId(UUID userId);
    List<Employee> findByDepartmentId(UUID departmentId);
    List<Employee> findByStatus(EmployeeStatus status);
    Boolean existsByUserId(UUID userId);
}