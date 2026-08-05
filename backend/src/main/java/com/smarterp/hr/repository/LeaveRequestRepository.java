package com.smarterp.hr.repository;

import com.smarterp.hr.domain.LeaveRequest;
import com.smarterp.hr.domain.LeaveStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface LeaveRequestRepository extends JpaRepository<LeaveRequest, UUID> {
    List<LeaveRequest> findByEmployeeId(UUID employeeId);
    List<LeaveRequest> findByStatus(LeaveStatus status);
    List<LeaveRequest> findByEmployeeIdAndStatus(UUID employeeId, LeaveStatus status);
}