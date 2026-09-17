package com.smarterp.analytics.repository;

import com.smarterp.analytics.dto.GenderPayGapDTO;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public class GenderPayGapRepository {

    private final JdbcTemplate jdbcTemplate;

    public GenderPayGapRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<GenderPayGapDTO> findSalaryByDepartmentTypeDivisionAndGender() {
        return jdbcTemplate.query(
            "SELECT department_type, division_description, gender, avg_salary, employee_count FROM v_gender_pay_gap",
            (rs, rowNum) -> new GenderPayGapDTO(
                rs.getString("department_type"),
                rs.getString("division_description"),
                rs.getString("gender"),
                rs.getBigDecimal("avg_salary") != null ? rs.getBigDecimal("avg_salary").doubleValue() : 0.0,
                rs.getLong("employee_count")
            )
        );
    }
}