package com.smarterp.hr.repository;

import com.smarterp.hr.domain.JobApplication;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface JobApplicationRepository
        extends JpaRepository<JobApplication, UUID> {
}