package com.smarterp.hr.repository;

import com.smarterp.hr.domain.LeaveRequest;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface LeaveRequestRepository extends JpaRepository<LeaveRequest, Long> {

    @EntityGraph(attributePaths = {"employee"})
    List<LeaveRequest> findByEmployeeEmployeeIdOrderByStartDateDesc(Long employeeId);

    @EntityGraph(attributePaths = {"employee"})
    List<LeaveRequest> findByStatusOrderByCreatedAtAsc(String status);

    @EntityGraph(attributePaths = {"employee"})
    List<LeaveRequest> findTop200ByOrderByCreatedAtDesc();
}
