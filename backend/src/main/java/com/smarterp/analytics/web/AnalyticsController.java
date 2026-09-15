package com.smarterp.analytics.web;

import com.smarterp.analytics.dto.AttritionRiskIndicatorsDTO;
import com.smarterp.analytics.dto.DepartmentSalarySummaryDTO;
import com.smarterp.analytics.dto.DepartmentTurnoverDTO;
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
import org.springframework.http.ResponseEntity;
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
    public ResponseEntity<KpiSummaryDTO> getDashboardKpis() {
        return ResponseEntity.ok(analyticsService.getDashboardKpis());
    }

    @GetMapping("/turnover")
    public ResponseEntity<List<DepartmentTurnoverDTO>> getTurnoverStats() {
        return ResponseEntity.ok(analyticsService.getTopTurnoverStats());
    }

    @GetMapping("/salary-summary")
    public ResponseEntity<List<DepartmentSalarySummaryDTO>> getSalarySummary() {
        return ResponseEntity.ok(analyticsService.getSalaryDistributionSummary());
    }

    @GetMapping("/typeturnover")
    public ResponseEntity<List<DepartmentTypeTurnoverDTO>> getTurnoverTypeStats() {
        return ResponseEntity.ok(analyticsService.getDepartmentTypeTurnoverStats());
    }

    @GetMapping("/risk")
    public ResponseEntity<List<AttritionRiskIndicatorsDTO>> getRiskStats() {
        return ResponseEntity.ok(analyticsService.getAttritionRiskIndicatorsStats());
    }

    @GetMapping("/performance-engagement")
    public ResponseEntity<List<EmployeePerformanceEngagementDTO>> getPerformanceEngagementStats() {
        return ResponseEntity.ok(analyticsService.getEmployeePerformanceEngagementStats());
    }

    @GetMapping("/recruitment-funnel")
    public ResponseEntity<List<RecruitmentFunnelAtsDTO>> getRecruitmentFunnelStats() {
        return ResponseEntity.ok(analyticsService.getRecruitmentFunnelAtsStats());
    }

    @GetMapping("/training")
    public ResponseEntity<List<TrainingAnalyticsDTO>> getTrainingAnalyticsStats() {
        return ResponseEntity.ok(analyticsService.getTrainingAnalyticsStats());
    }

    @GetMapping("/top-performers")
    public ResponseEntity<List<TopPerformerBenchmarksDTO>> getTopPerformerBenchmarksStats() {
        return ResponseEntity.ok(analyticsService.getTopPerformerBenchmarksStats());
    }
    @GetMapping("/pay-gap")
public ResponseEntity<List<GenderPayGapDTO>> getGenderPayGapStats() {
    return ResponseEntity.ok(analyticsService.getGenderPayGapStats());
}

@GetMapping("/time-to-hire")
public ResponseEntity<List<TimeToHireDTO>> getTimeToHireStats() {
    return ResponseEntity.ok(analyticsService.getTimeToHireStats());
}
}