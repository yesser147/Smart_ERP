package com.smarterp.hr.repository;

import com.smarterp.hr.domain.PerformanceReview;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface PerformanceReviewRepository extends JpaRepository<PerformanceReview, Long> {
    List<PerformanceReview> findByEmployeeEmployeeIdOrderByReviewDateDesc(Long employeeId);
}
