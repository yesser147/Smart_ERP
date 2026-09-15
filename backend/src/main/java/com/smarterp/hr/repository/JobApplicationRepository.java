package com.smarterp.hr.repository;

import com.smarterp.hr.domain.JobApplication;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.UUID;

public interface JobApplicationRepository extends JpaRepository<JobApplication, UUID> {

    // Fetches applicant + jobPosting in the SAME query instead of one
    // extra SELECT per row (N+1) -- this is what was making
    // getAllJobApplications() slow enough to trigger a client abort.
    @Query("""
        SELECT ja FROM JobApplication ja
        JOIN FETCH ja.applicant
        JOIN FETCH ja.jobPosting
    """)
    List<JobApplication> findAllWithRelations();
}