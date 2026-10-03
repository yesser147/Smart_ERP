package com.smarterp.hr.web;

import com.smarterp.hr.dto.*;
import com.smarterp.hr.service.LeaveService;
import com.smarterp.hr.service.WorkforceService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/** HR side of reviews, leave requests and budget allocations. */
@RestController
@RequestMapping("/hr")
@RequiredArgsConstructor
public class WorkforceController {

    private final WorkforceService workforceService;
    private final LeaveService leaveService;

    @GetMapping("/employees/{id}/reviews")
    public List<PerformanceReviewDTO> reviews(@PathVariable Long id) {
        return workforceService.getReviews(id);
    }

    @PostMapping("/employees/{id}/reviews")
    public PerformanceReviewDTO addReview(@PathVariable Long id, @Valid @RequestBody PerformanceReviewCreateDTO req) {
        return workforceService.addReview(id, req);
    }

    @GetMapping("/leave-requests")
    public List<LeaveRequestDTO> leaveRequests(@RequestParam(required = false) String status) {
        return leaveService.list(status);
    }

    @PatchMapping("/leave-requests/{id}/approve")
    public LeaveRequestDTO approve(@PathVariable Long id) {
        return leaveService.decide(id, true);
    }

    @PatchMapping("/leave-requests/{id}/reject")
    public LeaveRequestDTO reject(@PathVariable Long id) {
        return leaveService.decide(id, false);
    }

    @GetMapping("/budget-allocations")
    public List<BudgetAllocationDTO> allocations() {
        return workforceService.getAllocations();
    }

    @PostMapping("/budget-allocations")
    public BudgetAllocationDTO approveAllocation(@Valid @RequestBody BudgetAllocationCreateDTO req) {
        return workforceService.approveAllocation(req);
    }
}
