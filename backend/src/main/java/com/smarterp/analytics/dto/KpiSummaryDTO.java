package com.smarterp.analytics.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class KpiSummaryDTO {
    private long totalEmployees;
    private long activeEmployees;
    private long departmentCount;
    private long openJobPostings;
    private double avgEngagement;
    private double companyTurnoverRate;
    private long highRiskCount;
}