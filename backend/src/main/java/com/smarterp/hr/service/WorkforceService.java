package com.smarterp.hr.service;

import com.smarterp.hr.domain.DepartmentBudgetAllocation;
import com.smarterp.hr.domain.Employee;
import com.smarterp.hr.domain.PerformanceReview;
import com.smarterp.hr.dto.*;
import com.smarterp.hr.repository.DepartmentBudgetAllocationRepository;
import com.smarterp.hr.repository.DepartmentRepository;
import com.smarterp.hr.repository.EmployeeRepository;
import com.smarterp.hr.repository.PerformanceReviewRepository;
import com.smarterp.security.repository.UserRepository;
import com.smarterp.shared.audit.AuditService;
import com.smarterp.shared.exception.ResourceNotFoundException;
import com.smarterp.shared.notification.NotificationService;
import com.smarterp.shared.security.CurrentUser;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.List;

/** Performance reviews and budget allocations. */
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class WorkforceService {

    private final EmployeeRepository employeeRepository;
    private final DepartmentRepository departmentRepository;
    private final PerformanceReviewRepository reviewRepository;
    private final DepartmentBudgetAllocationRepository allocationRepository;
    private final UserRepository userRepository;
    private final AuditService auditService;
    private final NotificationService notificationService;

    // ---------------- performance reviews

    public List<PerformanceReviewDTO> getReviews(Long employeeId) {
        return reviewRepository.findByEmployeeEmployeeIdOrderByReviewDateDesc(employeeId)
                .stream().map(PerformanceReviewDTO::fromEntity).toList();
    }

    @Transactional
    public PerformanceReviewDTO addReview(Long employeeId, PerformanceReviewCreateDTO req) {
        Employee employee = employeeRepository.findById(employeeId)
                .orElseThrow(() -> new ResourceNotFoundException("No employee with id " + employeeId));
        PerformanceReview review = new PerformanceReview();
        review.setEmployee(employee);
        review.setReviewer(CurrentUser.email());
        review.setReviewDate(LocalDate.now());
        review.setRating(req.rating());
        review.setComments(req.comments());
        PerformanceReview saved = reviewRepository.save(review);

        auditService.log("PERFORMANCE_REVIEW_ADDED", "employee", employeeId, "rating " + req.rating());
        notificationService.notifyEmployee(employeeId, "New performance review",
                "A performance review was added to your file (rating " + req.rating() + "/5).", "/dashboard/me");
        return PerformanceReviewDTO.fromEntity(saved);
    }

    // ---------------- budget allocations (approved what-if results)

    public List<BudgetAllocationDTO> getAllocations() {
        return allocationRepository.findTop100ByOrderByCreatedAtDesc()
                .stream().map(BudgetAllocationDTO::fromEntity).toList();
    }

    @Transactional
    public BudgetAllocationDTO approveAllocation(BudgetAllocationCreateDTO req) {
        DepartmentBudgetAllocation allocation = new DepartmentBudgetAllocation();
        allocation.setDepartment(departmentRepository.findById(req.departmentId())
                .orElseThrow(() -> new ResourceNotFoundException("No team with id " + req.departmentId())));
        allocation.setAllocatedBudget(req.allocatedBudget());
        allocation.setPredictedPerformance(req.predictedPerformance());
        allocation.setFiscalPeriod(req.fiscalPeriod() == null || req.fiscalPeriod().isBlank()
                ? "FY" + LocalDate.now().getYear() : req.fiscalPeriod());
        userRepository.findByEmail(CurrentUser.email()).ifPresent(u -> allocation.setApprovedBy(u.getId()));
        DepartmentBudgetAllocation saved = allocationRepository.save(allocation);

        auditService.log("BUDGET_ALLOCATION_APPROVED", "department", req.departmentId(),
                req.allocatedBudget() + " USD for " + allocation.getFiscalPeriod());
        return BudgetAllocationDTO.fromEntity(saved);
    }
}
