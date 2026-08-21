package com.smarterp.hr.repository;

import com.smarterp.hr.domain.EmployeeTraining;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface EmployeeTrainingRepository
        extends JpaRepository<EmployeeTraining, Long> {
}