package com.smarterp.hr.repository;

import com.smarterp.hr.domain.Department;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
import java.util.UUID;

public interface DepartmentRepository extends JpaRepository<Department, UUID> {
    Optional<Department> findByName(String name);
    Boolean existsByName(String name);
}