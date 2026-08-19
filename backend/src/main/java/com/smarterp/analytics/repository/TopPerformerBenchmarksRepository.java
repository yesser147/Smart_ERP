package com.smarterp.analytics.repository;
import com.smarterp.analytics.domain.DepartmentTurnoverView;
import com.smarterp.analytics.domain.TopPerformerBenchmarks;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

public interface TopPerformerBenchmarksRepository extends JpaRepository<TopPerformerBenchmarks,Long> {
    
}
