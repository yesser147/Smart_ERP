package com.smarterp.analytics.repository;

import com.smarterp.analytics.domain.DepartmentTurnoverView;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

@Repository
public interface DepartmentTurnoverRepository extends JpaRepository<DepartmentTurnoverView, Long> {

    @Query(value = "SELECT * FROM v_department_turnover ORDER BY turnover_rate_pct DESC LIMIT 10", nativeQuery = true)
    List<DepartmentTurnoverView> findTop10ByTurnoverRate();
}