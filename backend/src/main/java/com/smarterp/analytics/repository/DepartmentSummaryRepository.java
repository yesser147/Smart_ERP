package com.smarterp.analytics.repository;

import com.smarterp.analytics.dto.DepartmentSummaryDTO;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public class DepartmentSummaryRepository {

    private final JdbcTemplate jdbcTemplate;

    public DepartmentSummaryRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<DepartmentSummaryDTO> findAll() {
        return jdbcTemplate.query(
            "SELECT * FROM v_department_summary",
            (rs, rowNum) -> new DepartmentSummaryDTO(
                rs.getLong("department_id"),
                rs.getString("business_unit"),
                rs.getString("department_type"),
                rs.getString("division_description"),
                rs.getLong("headcount"),
                rs.getLong("total_ever_employed"),
                rs.getObject("avg_salary") != null ? rs.getDouble("avg_salary") : null,
                rs.getDouble("turnover_rate_pct"),
                rs.getLong("active_count"),
                rs.getLong("terminated_count")
            )
        );
    }
}