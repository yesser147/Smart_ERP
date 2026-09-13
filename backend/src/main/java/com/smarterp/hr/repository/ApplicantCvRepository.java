package com.smarterp.hr.repository;

import com.smarterp.hr.domain.Applicant;
import com.smarterp.hr.domain.ApplicantCv;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface ApplicantCvRepository extends JpaRepository<ApplicantCv, UUID> {

    Optional<ApplicantCv> findByApplicant(Applicant applicant);
}