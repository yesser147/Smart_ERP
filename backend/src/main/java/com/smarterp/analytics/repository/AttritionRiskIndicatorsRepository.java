package com.smarterp.analytics.repository;
import com.smarterp.analytics.domain.AttritionRiskIndicators;
import com.smarterp.analytics.domain.DepartmentTurnoverView;
import com.smarterp.analytics.domain.EmployeePerformanceEngagement;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

public interface AttritionRiskIndicatorsRepository extends JpaRepository<AttritionRiskIndicators, Long> 
 {

    
} 
