package com.smarterp.hr.repository;

import com.smarterp.hr.domain.ApplicationStatusHistory;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface ApplicationStatusHistoryRepository extends JpaRepository<ApplicationStatusHistory, Long> {
    List<ApplicationStatusHistory> findByApplicationIdOrderByChangedAtAsc(UUID applicationId);
}
