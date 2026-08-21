package com.smarterp.hr.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

public record SalaryHistoryDTO(

    Long id,
    Long employeeId,
    LocalDate effectiveDate,
    BigDecimal salary,
    String currency,
    String changeReason

) {

    public static SalaryHistoryDTO fromEntity(
            com.smarterp.hr.domain.SalaryHistory entity) {

        return new SalaryHistoryDTO(
            entity.getId(),

            entity.getEmployee() != null
                ? entity.getEmployee().getEmployeeId()
                : null,

            entity.getEffectiveDate(),
            entity.getSalary(),
            entity.getCurrency(),
            entity.getChangeReason()
        );
    }
}