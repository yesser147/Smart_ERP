package com.smarterp.hr.dto;

import com.smarterp.hr.domain.PerformanceReview;

import java.time.LocalDate;

public record PerformanceReviewDTO(Long id, Long employeeId, String reviewer, LocalDate reviewDate,
                                   Integer rating, String comments) {

    public static PerformanceReviewDTO fromEntity(PerformanceReview r) {
        return new PerformanceReviewDTO(r.getId(), r.getEmployee().getEmployeeId(), r.getReviewer(),
                r.getReviewDate(), r.getRating(), r.getComments());
    }
}
