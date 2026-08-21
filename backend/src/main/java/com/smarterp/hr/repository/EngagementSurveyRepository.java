package com.smarterp.hr.repository;

import com.smarterp.hr.domain.EngagementSurvey;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface EngagementSurveyRepository
        extends JpaRepository<EngagementSurvey, Long> {
}