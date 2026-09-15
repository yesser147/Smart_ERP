package com.smarterp.analytics.service;

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
import com.smarterp.analytics.repository.AttritionRiskIndicatorsRepository;
import com.smarterp.analytics.repository.DepartmentTurnoverRepository;
import com.smarterp.analytics.repository.DepartmentTypeTurnoverRepository;
import com.smarterp.analytics.repository.EmployeePerformanceEngagementRepository;
import com.smarterp.analytics.repository.GenderPayGapRepository;
import com.smarterp.analytics.repository.RecruitmentFunnelAtsRepository;
import com.smarterp.analytics.repository.SalaryDistributionRepository;
import com.smarterp.analytics.repository.TimeToHireRepository;
import com.smarterp.analytics.repository.TopPerformerBenchmarksRepository;
import com.smarterp.analytics.repository.TrainingAnalyticsRepository;
import com.smarterp.hr.repository.DepartmentRepository;
import com.smarterp.hr.repository.EmployeeRepository;
import com.smarterp.hr.repository.JobPostingRepository;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AnalyticsService {

    private static final Logger log = LoggerFactory.getLogger(AnalyticsService.class);

    private final DepartmentTurnoverRepository turnoverRepository;
    private final DepartmentTypeTurnoverRepository departmentTypeTurnoverRepository;
    private final EmployeePerformanceEngagementRepository employeePerformanceEngagementRepository;
    private final SalaryDistributionRepository salaryDistributionRepository;
    private final RecruitmentFunnelAtsRepository recruitmentFunnelAtsRepository;
    private final TrainingAnalyticsRepository trainingAnalyticsRepository;
    private final AttritionRiskIndicatorsRepository attritionRiskIndicatorsRepository;
    private final TopPerformerBenchmarksRepository topPerformerBenchmarksRepository;
    private final GenderPayGapRepository genderPayGapRepository;
    private final TimeToHireRepository timeToHireRepository;
    private final JobPostingRepository jobPostingRepository;
    private final EmployeeRepository employeeRepository;
    private final DepartmentRepository departmentRepository;

    // Points at the FastAPI AI microservice. Set ai.service.base-url in
    // application.properties (e.g. ai.service.base-url=http://localhost:8000).
    @Value("${ai.service.base-url:http://localhost:8000}")
    private String aiServiceBaseUrl;

    private RestClient restClient() {
        return RestClient.create(aiServiceBaseUrl);
    }

    @Transactional(readOnly = true)
    public KpiSummaryDTO getDashboardKpis() {
        long totalEmployees = employeeRepository.countByIsDeletedFalse();

        long totalActive = employeeRepository.countByIsDeletedFalseAndEmployeeStatusIn(
            List.of("Active", "On Leave")
        );

        long totalTerminated = employeeRepository.countByIsDeletedFalseAndEmployeeStatusIn(
            List.of("Terminated", "Terminated For Cause", "Voluntarily Terminated")
        );

        double denominator = (double) (totalActive + totalTerminated);
        double companyTurnover = (denominator > 0)
                ? ((double) totalTerminated / denominator) * 100.0
                : 0.0;

        var riskList = attritionRiskIndicatorsRepository.findAll();

        double avgEngagement = riskList.stream()
                .mapToDouble(r -> r.getRecentEngagement() != null ? r.getRecentEngagement().doubleValue() : 0.0)
                .average()
                .orElse(0.0);

        long highRiskCount = fetchMlHighRiskCount()
                .orElseGet(() -> {
                    // Fallback: SQL heuristic, only used if the Python AI
                    // service is unreachable -- keeps the dashboard alive
                    // during a demo instead of hard-failing, but this is
                    // NOT the model's real prediction.
                    log.warn("AI service unreachable -- falling back to SQL heuristic for highRiskCount");
                    return riskList.stream()
                            .filter(r -> "HIGH".equalsIgnoreCase(r.getHeuristicRiskLevel()))
                            .count();
                });

        long openJobs = jobPostingRepository.countByStatusIgnoreCase("OPEN");
        long departmentCount = departmentRepository.count();

        return KpiSummaryDTO.builder()
                .totalEmployees(totalEmployees)
                .activeEmployees(totalActive)
                .departmentCount(departmentCount)
                .openJobPostings(openJobs)
                .avgEngagement(Math.round(avgEngagement * 10.0) / 10.0)
                .companyTurnoverRate(Math.round(companyTurnover * 10.0) / 10.0)
                .highRiskCount(highRiskCount)
                .build();
    }

    /**
     * Calls the real XGBoost model's risk scores (no LLM call, cheap) instead
     * of the SQL threshold heuristic in v_attrition_risk_indicators. Returns
     * empty on any failure so the caller can fall back gracefully.
     */
    private java.util.Optional<Long> fetchMlHighRiskCount() {
        try {
            Map<String, Object> response = restClient()
                    .get()
                    .uri("/api/ai/retention-risk-scores")
                    .retrieve()
                    .body(Map.class);

            if (response != null && response.get("high_risk_count") != null) {
                return java.util.Optional.of(((Number) response.get("high_risk_count")).longValue());
            }
            return java.util.Optional.empty();
        } catch (Exception e) {
            log.warn("Failed to fetch ML risk scores from AI service: {}", e.getMessage());
            return java.util.Optional.empty();
        }
    }

    public List<DepartmentTurnoverDTO> getTopTurnoverStats() {
        return turnoverRepository.findTop10ByTurnoverRate()
                .stream()
                .map(DepartmentTurnoverDTO::fromEntity)
                .collect(Collectors.toList());
    }

    public List<DepartmentSalarySummaryDTO> getSalaryDistributionSummary() {
        return salaryDistributionRepository.findSalarySummaryByBusinessUnit();
    }

    public List<DepartmentTypeTurnoverDTO> getDepartmentTypeTurnoverStats() {
        return departmentTypeTurnoverRepository.findAll()
                .stream()
                .map(DepartmentTypeTurnoverDTO::fromEntity)
                .collect(Collectors.toList());
    }

    public List<EmployeePerformanceEngagementDTO> getEmployeePerformanceEngagementStats() {
        return employeePerformanceEngagementRepository.findAll()
                .stream()
                .map(EmployeePerformanceEngagementDTO::fromEntity)
                .collect(Collectors.toList());
    }

    public List<RecruitmentFunnelAtsDTO> getRecruitmentFunnelAtsStats() {
        return recruitmentFunnelAtsRepository.findAll()
                .stream()
                .map(RecruitmentFunnelAtsDTO::fromEntity)
                .collect(Collectors.toList());
    }

    public List<TrainingAnalyticsDTO> getTrainingAnalyticsStats() {
        return trainingAnalyticsRepository.findAll()
                .stream()
                .map(TrainingAnalyticsDTO::fromEntity)
                .collect(Collectors.toList());
    }

    public List<AttritionRiskIndicatorsDTO> getAttritionRiskIndicatorsStats() {
        return attritionRiskIndicatorsRepository.findAll()
                .stream()
                .map(AttritionRiskIndicatorsDTO::fromEntity)
                .collect(Collectors.toList());
    }

    public List<TopPerformerBenchmarksDTO> getTopPerformerBenchmarksStats() {
        return topPerformerBenchmarksRepository.findAll()
                .stream()
                .map(TopPerformerBenchmarksDTO::fromEntity)
                .collect(Collectors.toList());
    }

    // NEW
    public List<GenderPayGapDTO> getGenderPayGapStats() {
        return genderPayGapRepository.findSalaryByBusinessUnitAndGender();
    }

    // NEW
    public List<TimeToHireDTO> getTimeToHireStats() {
        return timeToHireRepository.findAvgTimeToHirePerJob();
    }
}