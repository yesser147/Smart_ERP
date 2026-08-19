package com.smarterp.analytics.repository;
import com.smarterp.analytics.domain.DepartmentTurnoverView;
import com.smarterp.analytics.domain.RecruitmentFunnelAts;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;


public interface RecruitmentFunnelAtsRepository extends JpaRepository<RecruitmentFunnelAts,Long> {
    
}
