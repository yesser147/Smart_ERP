package com.smarterp.hr.repository;

import com.smarterp.hr.domain.JobPosting;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface JobPostingRepository
        extends JpaRepository<JobPosting, Long> {
}