package com.smarterp.hr.repository;

import com.smarterp.hr.domain.SalaryHistory;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SalaryHistoryRepository extends JpaRepository<SalaryHistory, Long> {

    List<SalaryHistory> findByEmployeeEmployeeIdOrderByEffectiveDateDesc(Long employeeId);
}
