package com.smarterp.analytics.web;

import com.smarterp.analytics.dto.AttritionRiskIndicatorsDTO;
import com.smarterp.analytics.dto.DepartmentTurnoverDTO;
import com.smarterp.analytics.dto.DepartmentTypeTurnoverDTO;
import com.smarterp.analytics.dto.EmployeePerformanceEngagementDTO;
import com.smarterp.analytics.dto.RecruitmentFunnelAtsDTO;
import com.smarterp.analytics.dto.SalaryDistributionDTO;
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

    @GetMapping("/turnover")
    public ResponseEntity<List<DepartmentTurnoverDTO>> getTurnoverStats() {
        return ResponseEntity.ok(
                analyticsService.getDepartmentTurnoverStats()
        );
    }
    @GetMapping("/typeturnover")
    public ResponseEntity<List<DepartmentTypeTurnoverDTO>> getTurnoverTypeStats() {
        return ResponseEntity.ok(
                analyticsService.getDepartmentTypeTurnoverStats()
        );
    }


    @GetMapping("/risk")
    public ResponseEntity<List<AttritionRiskIndicatorsDTO>> getRiskStats() {
        return ResponseEntity.ok(
                analyticsService.getAttritionRiskIndicatorsStats()
        );
    }

    @GetMapping("/performance-engagement")
    public ResponseEntity<List<EmployeePerformanceEngagementDTO>> getPerformanceEngagementStats() {
        return ResponseEntity.ok(
                analyticsService.getEmployeePerformanceEngagementStats()
        );
    }

    @GetMapping("/salary-distribution")
    public ResponseEntity<List<SalaryDistributionDTO>> getSalaryDistributionStats() {
        return ResponseEntity.ok(
                analyticsService.getSalaryDistributionStats()
        );
    }

    @GetMapping("/recruitment-funnel")
    public ResponseEntity<List<RecruitmentFunnelAtsDTO>> getRecruitmentFunnelStats() {
        return ResponseEntity.ok(
                analyticsService.getRecruitmentFunnelAtsStats()
        );
    }

    @GetMapping("/training")
    public ResponseEntity<List<TrainingAnalyticsDTO>> getTrainingAnalyticsStats() {
        return ResponseEntity.ok(
                analyticsService.getTrainingAnalyticsStats()
        );
    }

    @GetMapping("/top-performers")
    public ResponseEntity<List<TopPerformerBenchmarksDTO>> getTopPerformerBenchmarksStats() {
        return ResponseEntity.ok(
                analyticsService.getTopPerformerBenchmarksStats()
        );
    }
}