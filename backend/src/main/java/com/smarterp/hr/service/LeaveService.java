package com.smarterp.hr.service;

import com.smarterp.hr.domain.Employee;
import com.smarterp.hr.domain.LeaveRequest;
import com.smarterp.hr.dto.LeaveRequestCreateDTO;
import com.smarterp.hr.dto.LeaveRequestDTO;
import com.smarterp.hr.repository.EmployeeRepository;
import com.smarterp.hr.repository.LeaveRequestRepository;
import com.smarterp.shared.audit.AuditService;
import com.smarterp.shared.exception.BadRequestException;
import com.smarterp.shared.exception.ResourceNotFoundException;
import com.smarterp.shared.notification.NotificationService;
import com.smarterp.shared.security.CurrentUser;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class LeaveService {

    private final LeaveRequestRepository repository;
    private final EmployeeRepository employeeRepository;
    private final NotificationService notificationService;
    private final AuditService auditService;

    public List<LeaveRequestDTO> forEmployee(Long employeeId) {
        return repository.findByEmployeeEmployeeIdOrderByStartDateDesc(employeeId)
                .stream().map(LeaveRequestDTO::fromEntity).toList();
    }

    public List<LeaveRequestDTO> list(String status) {
        var rows = status == null || status.isBlank()
                ? repository.findTop200ByOrderByCreatedAtDesc()
                : repository.findByStatusOrderByCreatedAtAsc(status.toUpperCase());
        return rows.stream().map(LeaveRequestDTO::fromEntity).toList();
    }

    @Transactional
    public LeaveRequestDTO request(Long employeeId, LeaveRequestCreateDTO req) {
        if (req.endDate().isBefore(req.startDate())) {
            throw new BadRequestException("The end date is before the start date.");
        }
        if (req.startDate().isBefore(java.time.LocalDate.now())) {
            throw new BadRequestException("Leave cannot start in the past.");
        }
        Employee employee = employeeRepository.findById(employeeId)
                .orElseThrow(() -> new ResourceNotFoundException("No employee with id " + employeeId));
        String status = employee.getEmployeeStatus() == null ? "" : employee.getEmployeeStatus();
        if (!status.equalsIgnoreCase("Active") && !status.equalsIgnoreCase("On Leave")) {
            throw new BadRequestException("Only current employees can request leave.");
        }
        LeaveRequest leave = new LeaveRequest();
        leave.setEmployee(employee);
        leave.setLeaveType(req.leaveType());
        leave.setStartDate(req.startDate());
        leave.setEndDate(req.endDate());
        leave.setReason(req.reason());
        LeaveRequest saved = repository.save(leave);

        notificationService.notifyHr("New leave request",
                employee.getFirstName() + " " + employee.getLastName() + " requested " + req.leaveType().toLowerCase()
                        + " leave from " + req.startDate() + " to " + req.endDate() + ".", "/dashboard/leave");
        return LeaveRequestDTO.fromEntity(saved);
    }

    @Transactional
    public LeaveRequestDTO decide(Long id, boolean approve) {
        LeaveRequest leave = repository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("No leave request with id " + id));
        if (!"PENDING".equals(leave.getStatus())) {
            throw new BadRequestException("This request was already " + leave.getStatus().toLowerCase() + ".");
        }
        leave.setStatus(approve ? "APPROVED" : "REJECTED");
        leave.setDecidedBy(CurrentUser.email());
        leave.setDecidedAt(LocalDateTime.now());

        Employee e = leave.getEmployee();
        auditService.log("LEAVE_" + leave.getStatus(), "leave_request", id,
                e.getFirstName() + " " + e.getLastName() + ", " + leave.getStartDate() + " to " + leave.getEndDate());
        notificationService.notifyEmployee(e.getEmployeeId(), "Leave request " + leave.getStatus().toLowerCase(),
                "Your " + leave.getLeaveType().toLowerCase() + " leave from " + leave.getStartDate() + " to "
                        + leave.getEndDate() + " was " + leave.getStatus().toLowerCase() + ".", "/dashboard/me");
        return LeaveRequestDTO.fromEntity(leave);
    }
}
