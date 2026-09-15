package com.smarterp.hr.repository;

import com.smarterp.hr.domain.Applicant;
import com.smarterp.hr.domain.ApplicantCv;
import com.smarterp.hr.dto.ApplicantCvStatusView;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface ApplicantCvRepository extends JpaRepository<ApplicantCv, java.util.UUID> {

    // keep your existing method used elsewhere (PublicApplicationService)
    Optional<ApplicantCv> findByApplicant(Applicant applicant);

    // NEW: batched, and never touches the vector column's value directly
    @Query("""
        select new com.smarterp.hr.dto.ApplicantCvStatusView(
            a.applicantId,
            case when c.fileUrl is not null then true else false end,
            case when c.cvEmbedding is not null then true else false end
        )
        from Applicant a
        left join ApplicantCv c on c.applicant = a
        """)
    List<ApplicantCvStatusView> findAllCvStatus();
}