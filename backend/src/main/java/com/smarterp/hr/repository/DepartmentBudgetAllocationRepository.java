package com.smarterp.hr.repository;

import com.smarterp.hr.domain.DepartmentBudgetAllocation;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface DepartmentBudgetAllocationRepository extends JpaRepository<DepartmentBudgetAllocation, Long> {

    @EntityGraph(attributePaths = {"department"})
    List<DepartmentBudgetAllocation> findTop100ByOrderByCreatedAtDesc();
}
