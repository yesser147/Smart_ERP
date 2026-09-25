package com.smarterp.hr.repository;

import com.smarterp.hr.domain.JobApplication;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.UUID;

public interface JobApplicationRepository extends JpaRepository<JobApplication, UUID> {

    @Query("""
        SELECT ja FROM JobApplication ja
        JOIN FETCH ja.applicant
        JOIN FETCH ja.jobPosting jp
        WHERE jp.jobId = :jobId
    """)
    List<JobApplication> findByJobIdWithRelations(@Param("jobId") Long jobId);

    @Query("""
        SELECT ja FROM JobApplication ja
        JOIN FETCH ja.applicant a
        JOIN FETCH ja.jobPosting
        WHERE a.applicantId = :applicantId
    """)
    List<JobApplication> findByApplicantIdWithRelations(@Param("applicantId") Long applicantId);

    /** [jobId, number of applications] for every posting that has applications. */
    @Query("SELECT ja.jobPosting.jobId, COUNT(ja) FROM JobApplication ja GROUP BY ja.jobPosting.jobId")
    List<Object[]> countByJob();

    Long countByJobPostingJobId(Long jobId);
}
