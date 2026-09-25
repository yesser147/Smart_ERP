package com.smarterp.analytics.web;

import com.smarterp.analytics.dto.DepartmentSalarySummaryDTO;
import com.smarterp.analytics.dto.DepartmentSummaryDTO;
import com.smarterp.analytics.dto.DepartmentTypeTurnoverDTO;
import com.smarterp.analytics.dto.EmployeePerformanceEngagementDTO;
import com.smarterp.analytics.dto.GenderPayGapDTO;
import com.smarterp.analytics.dto.KpiSummaryDTO;
import com.smarterp.analytics.dto.RecruitmentFunnelAtsDTO;
import com.smarterp.analytics.dto.TimeToHireDTO;
import com.smarterp.analytics.dto.TopPerformerBenchmarksDTO;
import com.smarterp.analytics.dto.TrainingAnalyticsDTO;
import com.smarterp.analytics.service.AnalyticsService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/analytics")
@RequiredArgsConstructor
public class AnalyticsController {

    private final AnalyticsService analyticsService;

    @GetMapping("/kpis")
    public KpiSummaryDTO kpis() {
        return analyticsService.getDashboardKpis();
    }

    @GetMapping("/salary-summary")
    public List<DepartmentSalarySummaryDTO> salarySummary() {
        return analyticsService.getSalaryDistributionSummary();
    }

    @GetMapping("/typeturnover")
    public List<DepartmentTypeTurnoverDTO> turnoverByDepartmentType() {
        return analyticsService.getDepartmentTypeTurnoverStats();
    }

    @GetMapping("/performance-engagement")
    public List<EmployeePerformanceEngagementDTO> performanceEngagement() {
        return analyticsService.getEmployeePerformanceEngagementStats();
    }

    @GetMapping("/recruitment-funnel")
    public List<RecruitmentFunnelAtsDTO> recruitmentFunnel() {
        return analyticsService.getRecruitmentFunnelAtsStats();
    }

    @GetMapping("/training")
    public List<TrainingAnalyticsDTO> training() {
        return analyticsService.getTrainingAnalyticsStats();
    }

    @GetMapping("/top-performers")
    public List<TopPerformerBenchmarksDTO> topPerformers() {
        return analyticsService.getTopPerformerBenchmarksStats();
    }

    @GetMapping("/pay-gap")
    public List<GenderPayGapDTO> payGap() {
        return analyticsService.getGenderPayGapStats();
    }

    @GetMapping("/time-to-hire")
    public List<TimeToHireDTO> timeToHire() {
        return analyticsService.getTimeToHireStats();
    }

    @GetMapping("/department-summary")
    public List<DepartmentSummaryDTO> departmentSummary() {
        return analyticsService.getDepartmentSummary();
    }
}
