package com.smarterp.hr.repository;

import com.smarterp.hr.domain.Attendance;
import org.springframework.data.jpa.repository.JpaRepository;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface AttendanceRepository extends JpaRepository<Attendance, UUID> {
    List<Attendance> findByEmployeeId(UUID employeeId);
    Optional<Attendance> findByEmployeeIdAndWorkDate(UUID employeeId, LocalDate workDate);
    List<Attendance> findByWorkDate(LocalDate workDate);
}