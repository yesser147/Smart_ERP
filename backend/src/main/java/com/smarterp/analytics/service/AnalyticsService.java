package com.smarterp.analytics.service;

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
import com.smarterp.analytics.repository.AttritionRiskIndicatorsRepository;
import com.smarterp.analytics.repository.DepartmentSummaryRepository;
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
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/** Read-only analytics served from the BI views (R__create_bi_views.sql). */
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AnalyticsService {

    private final DepartmentTypeTurnoverRepository departmentTypeTurnoverRepository;
    private final EmployeePerformanceEngagementRepository employeePerformanceEngagementRepository;
    private final SalaryDistributionRepository salaryDistributionRepository;
    private final RecruitmentFunnelAtsRepository recruitmentFunnelAtsRepository;
    private final TrainingAnalyticsRepository trainingAnalyticsRepository;
    private final AttritionRiskIndicatorsRepository attritionRiskIndicatorsRepository;
    private final TopPerformerBenchmarksRepository topPerformerBenchmarksRepository;
    private final GenderPayGapRepository genderPayGapRepository;
    private final TimeToHireRepository timeToHireRepository;
    private final DepartmentSummaryRepository departmentSummaryRepository;
    private final JobPostingRepository jobPostingRepository;
    private final EmployeeRepository employeeRepository;
    private final DepartmentRepository departmentRepository;

    /** The flight-risk count is not here: the dashboard asks the AI engine (ML model) directly. */
    public KpiSummaryDTO getDashboardKpis() {
        long totalEmployees = employeeRepository.countByIsDeletedFalse();
        long totalActive = employeeRepository.countByIsDeletedFalseAndEmployeeStatusIn(List.of("Active", "On Leave"));
        long totalTerminated = employeeRepository.countByIsDeletedFalseAndEmployeeStatusIn(
                List.of("Terminated", "Terminated For Cause", "Voluntarily Terminated"));

        double denominator = totalActive + totalTerminated;
        double companyTurnover = denominator > 0 ? totalTerminated / denominator * 100.0 : 0.0;

        double avgEngagement = attritionRiskIndicatorsRepository.findAll().stream()
                .mapToDouble(r -> r.getRecentEngagement() != null ? r.getRecentEngagement().doubleValue() : 0.0)
                .average()
                .orElse(0.0);

        return KpiSummaryDTO.builder()
                .totalEmployees(totalEmployees)
                .activeEmployees(totalActive)
                .departmentCount(departmentRepository.count())
                .openJobPostings(jobPostingRepository.countByStatusIgnoreCase("OPEN"))
                .avgEngagement(Math.round(avgEngagement * 10.0) / 10.0)
                .companyTurnoverRate(Math.round(companyTurnover * 10.0) / 10.0)
                .build();
    }

    public List<DepartmentSalarySummaryDTO> getSalaryDistributionSummary() {
        return salaryDistributionRepository.findSalarySummaryByDivision();
    }

    public List<DepartmentTypeTurnoverDTO> getDepartmentTypeTurnoverStats() {
        return departmentTypeTurnoverRepository.findAll().stream().map(DepartmentTypeTurnoverDTO::fromEntity).toList();
    }

    public List<EmployeePerformanceEngagementDTO> getEmployeePerformanceEngagementStats() {
        return employeePerformanceEngagementRepository.findAll().stream().map(EmployeePerformanceEngagementDTO::fromEntity).toList();
    }

    public List<RecruitmentFunnelAtsDTO> getRecruitmentFunnelAtsStats() {
        return recruitmentFunnelAtsRepository.findAll().stream().map(RecruitmentFunnelAtsDTO::fromEntity).toList();
    }

    public List<TrainingAnalyticsDTO> getTrainingAnalyticsStats() {
        return trainingAnalyticsRepository.findAll().stream().map(TrainingAnalyticsDTO::fromEntity).toList();
    }

    public List<TopPerformerBenchmarksDTO> getTopPerformerBenchmarksStats() {
        return topPerformerBenchmarksRepository.findAll().stream().map(TopPerformerBenchmarksDTO::fromEntity).toList();
    }

    public List<GenderPayGapDTO> getGenderPayGapStats() {
        return genderPayGapRepository.findSalaryByDepartmentTypeDivisionAndGender();
    }

    public List<TimeToHireDTO> getTimeToHireStats() {
        return timeToHireRepository.findAvgTimeToHirePerJob();
    }

    public List<DepartmentSummaryDTO> getDepartmentSummary() {
        return departmentSummaryRepository.findAll();
    }
}
