package com.smarterp.analytics.service;

import com.smarterp.analytics.dto.AttritionRiskIndicatorsDTO;
import com.smarterp.analytics.dto.DepartmentSalarySummaryDTO;
import com.smarterp.analytics.dto.DepartmentTurnoverDTO;
import com.smarterp.analytics.dto.DepartmentTypeTurnoverDTO;
import com.smarterp.analytics.dto.EmployeePerformanceEngagementDTO;
import com.smarterp.analytics.dto.KpiSummaryDTO;
import com.smarterp.analytics.dto.RecruitmentFunnelAtsDTO;
import com.smarterp.analytics.dto.TopPerformerBenchmarksDTO;
import com.smarterp.analytics.dto.TrainingAnalyticsDTO;
import com.smarterp.analytics.repository.AttritionRiskIndicatorsRepository;
import com.smarterp.analytics.repository.DepartmentTurnoverRepository;
import com.smarterp.analytics.repository.DepartmentTypeTurnoverRepository;
import com.smarterp.analytics.repository.EmployeePerformanceEngagementRepository;
import com.smarterp.analytics.repository.RecruitmentFunnelAtsRepository;
import com.smarterp.analytics.repository.SalaryDistributionRepository;
import com.smarterp.analytics.repository.TopPerformerBenchmarksRepository;
import com.smarterp.analytics.repository.TrainingAnalyticsRepository;
import com.smarterp.hr.repository.DepartmentRepository;
import com.smarterp.hr.repository.EmployeeRepository;
import com.smarterp.hr.repository.JobPostingRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AnalyticsService {

    private final DepartmentTurnoverRepository turnoverRepository;
    private final DepartmentTypeTurnoverRepository departmentTypeTurnoverRepository;
    private final EmployeePerformanceEngagementRepository employeePerformanceEngagementRepository;
    private final SalaryDistributionRepository salaryDistributionRepository;
    private final RecruitmentFunnelAtsRepository recruitmentFunnelAtsRepository;
    private final TrainingAnalyticsRepository trainingAnalyticsRepository;
    private final AttritionRiskIndicatorsRepository attritionRiskIndicatorsRepository;
    private final TopPerformerBenchmarksRepository topPerformerBenchmarksRepository;
    private final JobPostingRepository jobPostingRepository;
    private final EmployeeRepository employeeRepository;
    private final DepartmentRepository departmentRepository;

    @Transactional(readOnly = true)
public KpiSummaryDTO getDashboardKpis() {
    // 1. Direct DB counts (Includes Future Start, On Leave, and unassigned staff)
    long totalEmployees = employeeRepository.countByIsDeletedFalse();
    
    long totalActive = employeeRepository.countByIsDeletedFalseAndEmployeeStatusIn(
        List.of("Active", "On Leave")
    );
    
    long totalTerminated = employeeRepository.countByIsDeletedFalseAndEmployeeStatusIn(
        List.of("Terminated", "Terminated For Cause", "Voluntarily Terminated")
    );

    // 2. Turnover calculation based on historical active + terminated pool
    double denominator = (double) (totalActive + totalTerminated);
    double companyTurnover = (denominator > 0)
            ? ((double) totalTerminated / denominator) * 100.0
            : 0.0;

    // 3. Risk & Engagement Metrics
    var riskList = attritionRiskIndicatorsRepository.findAll();
    
    double avgEngagement = riskList.stream()
            .mapToDouble(r -> r.getRecentEngagement() != null ? r.getRecentEngagement().doubleValue() : 0.0)
            .average()
            .orElse(0.0);

    long highRiskCount = riskList.stream()
            .filter(r -> "HIGH".equalsIgnoreCase(r.getHeuristicRiskLevel()))
            .count();

    long openJobs = jobPostingRepository.countByStatusIgnoreCase("OPEN");
    long departmentCount = departmentRepository.count();

    return KpiSummaryDTO.builder()
            .totalEmployees(totalEmployees) // Returns exact 3,000
            .activeEmployees(totalActive)   // Returns exact 1,553
            .departmentCount(departmentCount)
            .openJobPostings(openJobs)
            .avgEngagement(Math.round(avgEngagement * 10.0) / 10.0)
            .companyTurnoverRate(Math.round(companyTurnover * 10.0) / 10.0)
            .highRiskCount(highRiskCount)
            .build();
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
}