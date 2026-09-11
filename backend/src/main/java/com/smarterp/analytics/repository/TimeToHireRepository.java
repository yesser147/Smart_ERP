package com.smarterp.analytics.repository;

import com.smarterp.analytics.dto.TimeToHireDTO;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public class TimeToHireRepository {

    private final JdbcTemplate jdbcTemplate;

    public TimeToHireRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<TimeToHireDTO> findAvgTimeToHirePerJob() {
        return jdbcTemplate.query(
            "SELECT job_id, job_title, department_id, avg_days_to_hire, hired_count FROM v_time_to_hire",
            (rs, rowNum) -> new TimeToHireDTO(
                rs.getLong("job_id"),
                rs.getString("job_title"),
                rs.getLong("department_id"),
                rs.getDouble("avg_days_to_hire"),
                rs.getLong("hired_count")
            )
        );
    }
}