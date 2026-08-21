package com.smarterp.analytics.service;

import com.smarterp.analytics.domain.DepartmentTypeTurnover;
import com.smarterp.analytics.dto.AttritionRiskIndicatorsDTO;
import com.smarterp.analytics.dto.DepartmentTurnoverDTO;
import com.smarterp.analytics.dto.DepartmentTypeTurnoverDTO;
import com.smarterp.analytics.dto.EmployeePerformanceEngagementDTO;
import com.smarterp.analytics.dto.RecruitmentFunnelAtsDTO;
import com.smarterp.analytics.dto.SalaryDistributionDTO;
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

    private final EmployeePerformanceEngagementRepository employeePerformanceEngagementRepository;

    private final SalaryDistributionRepository salaryDistributionRepository;

    private final RecruitmentFunnelAtsRepository recruitmentFunnelAtsRepository;

    private final TrainingAnalyticsRepository trainingAnalyticsRepository;

    private final AttritionRiskIndicatorsRepository attritionRiskIndicatorsRepository;

    private final TopPerformerBenchmarksRepository topPerformerBenchmarksRepository;
    private final DepartmentTypeTurnoverRepository departmentTypeTurnoverRepository;


    
    public List<DepartmentTurnoverDTO> getDepartmentTurnoverStats() {
        return turnoverRepository.findAll()
                .stream()
                .map(DepartmentTurnoverDTO::fromEntity)
                .collect(Collectors.toList());
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


   
    public List<SalaryDistributionDTO> getSalaryDistributionStats() {
        return salaryDistributionRepository.findAll()
                .stream()
                .map(SalaryDistributionDTO::fromEntity)
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