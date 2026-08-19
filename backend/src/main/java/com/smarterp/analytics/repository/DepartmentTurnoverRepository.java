package com.smarterp.analytics.repository;

import com.smarterp.analytics.domain.DepartmentTurnoverView;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface DepartmentTurnoverRepository extends JpaRepository<DepartmentTurnoverView, Long> {

}