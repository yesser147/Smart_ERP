package com.smarterp.hr.repository;

import com.smarterp.hr.domain.ApplicantCv;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface ApplicantCvRepository
        extends JpaRepository<ApplicantCv, UUID> {
}