package com.smarterp.hr.repository;

import com.smarterp.hr.domain.EmployeeTraining;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface EmployeeTrainingRepository
        extends JpaRepository<EmployeeTraining, Long> {

    List<EmployeeTraining> findByEmployeeEmployeeIdOrderByTrainingDateDesc(Long employeeId);
}
