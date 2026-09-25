package com.smarterp.hr.repository;

import com.smarterp.hr.domain.EngagementSurvey;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface EngagementSurveyRepository
        extends JpaRepository<EngagementSurvey, Long> {

    List<EngagementSurvey> findByEmployeeEmployeeIdOrderBySurveyDateDesc(Long employeeId);
}
