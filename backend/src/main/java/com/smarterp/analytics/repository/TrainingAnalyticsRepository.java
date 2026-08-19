package com.smarterp.analytics.repository;

import com.smarterp.analytics.domain.DepartmentTurnoverView;
import com.smarterp.analytics.domain.TrainingAnalytics;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface TrainingAnalyticsRepository extends JpaRepository<TrainingAnalytics, Long> {

}