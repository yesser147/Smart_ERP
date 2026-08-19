package com.smarterp.analytics.dto;

import java.math.BigDecimal;

import com.smarterp.analytics.domain.SalaryDistribution;

public record SalaryDistributionDTO(

    Long departmentId,

    String businessUnit,

    String jobFunction,

    Long employeeCount,

    BigDecimal avgSalary,

    BigDecimal minSalary,

    BigDecimal maxSalary,

    BigDecimal totalPayrollBurden

) {

    public static SalaryDistributionDTO fromEntity(
            SalaryDistribution entity) {

        return new SalaryDistributionDTO(
            entity.getId().getDepartmentId(),
            entity.getBusinessUnit(),
            entity.getId().getJobFunction(),
            entity.getEmployeeCount(),
            entity.getAvgSalary(),
            entity.getMinSalary(),
            entity.getMaxSalary(),
            entity.getTotalPayrollBurden()
        );
    }
}