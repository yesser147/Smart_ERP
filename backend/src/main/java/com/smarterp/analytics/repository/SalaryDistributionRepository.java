package com.smarterp.analytics.repository;
import com.smarterp.analytics.domain.DepartmentTurnoverView;
import com.smarterp.analytics.domain.SalaryDistribution;
import com.smarterp.analytics.domain.SalaryDistributionId;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface SalaryDistributionRepository
        extends JpaRepository<SalaryDistribution, SalaryDistributionId> {
}