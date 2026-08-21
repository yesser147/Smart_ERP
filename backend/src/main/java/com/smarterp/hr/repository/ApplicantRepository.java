package com.smarterp.hr.repository;

import com.smarterp.hr.domain.Applicant;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ApplicantRepository
        extends JpaRepository<Applicant, Long> {
}