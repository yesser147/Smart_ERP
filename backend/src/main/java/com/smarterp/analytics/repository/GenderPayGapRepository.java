package com.smarterp.analytics.repository;

import com.smarterp.analytics.dto.GenderPayGapDTO;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.util.List;

@Repository
public class GenderPayGapRepository {

    private final JdbcTemplate jdbcTemplate;

    public GenderPayGapRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<GenderPayGapDTO> findSalaryByBusinessUnitAndGender() {
        return jdbcTemplate.query(
            "SELECT business_unit, gender, avg_salary, employee_count FROM v_gender_pay_gap",
            (rs, rowNum) -> new GenderPayGapDTO(
                rs.getString("business_unit"),
                rs.getString("gender"),
                rs.getBigDecimal("avg_salary") != null ? rs.getBigDecimal("avg_salary").doubleValue() : 0.0,
                rs.getLong("employee_count")
            )
        );
    }
}