package com.smarterp.hr.repository;

import com.smarterp.hr.domain.JobPosting;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface JobPostingRepository extends JpaRepository<JobPosting, Long> {

    // Add any other relationships JobPosting has to attributePaths (e.g., "hiringManager")
    @EntityGraph(attributePaths = {"department"})
    @Query("SELECT j FROM JobPosting j")
    List<JobPosting> findAllWithRelations();
    long countByStatusIgnoreCase(String status);
}