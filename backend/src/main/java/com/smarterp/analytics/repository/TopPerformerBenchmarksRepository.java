package com.smarterp.analytics.repository;
import com.smarterp.analytics.domain.TopPerformerBenchmarks;

import org.springframework.data.jpa.repository.JpaRepository;

public interface TopPerformerBenchmarksRepository extends JpaRepository<TopPerformerBenchmarks,Long> {
    
}
