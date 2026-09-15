package com.smarterp.analytics.repository;

import com.smarterp.analytics.domain.SalaryDistribution;
import com.smarterp.analytics.domain.SalaryDistributionId;
import com.smarterp.analytics.dto.DepartmentSalarySummaryDTO;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SalaryDistributionRepository extends JpaRepository<SalaryDistribution, SalaryDistributionId> {

    @Query("SELECT new com.smarterp.analytics.dto.DepartmentSalarySummaryDTO(" +
           "s.businessUnit, AVG(s.avgSalary)) " +
           "FROM SalaryDistribution s " +
           "GROUP BY s.businessUnit")
    List<DepartmentSalarySummaryDTO> findSalarySummaryByBusinessUnit();
}