package com.smarterp.hr.service;

import com.smarterp.hr.domain.Applicant;
import com.smarterp.hr.domain.ApplicantCv;
import com.smarterp.hr.domain.JobApplication;
import com.smarterp.hr.domain.JobPosting;
import com.smarterp.hr.dto.JobApplicationSubmissionDTO;
import com.smarterp.hr.repository.ApplicantCvRepository;
import com.smarterp.hr.repository.ApplicantRepository;
import com.smarterp.hr.repository.JobApplicationRepository;
import com.smarterp.hr.repository.JobPostingRepository;
import com.smarterp.shared.exception.ResourceNotFoundException;
import com.smarterp.shared.storage.MinioService;
import jakarta.persistence.EntityManager;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class PublicApplicationService {

    private final ApplicantRepository applicantRepository;
    private final ApplicantCvRepository applicantCvRepository;
    private final JobPostingRepository jobPostingRepository;
    private final JobApplicationRepository jobApplicationRepository;
    private final MinioService minioService;
    private final EntityManager entityManager; // NEW

    @Transactional
    public JobApplicationSubmissionDTO submitApplication(
            String firstName, String lastName, String email, String phoneNumber,
            String educationLevel, Long jobId, Double desiredSalary, MultipartFile cv
    ) {
        JobPosting job = jobPostingRepository.findById(jobId)
                .orElseThrow(() -> new ResourceNotFoundException("Aucune offre trouvée avec l'id : " + jobId));

        Applicant applicant = applicantRepository.findByEmail(email)
                .orElseGet(() -> {
                    Applicant a = new Applicant();
                    a.setFirstName(firstName);
                    a.setLastName(lastName);
                    a.setEmail(email);
                    a.setPhoneNumber(phoneNumber);
                    a.setEducationLevel(educationLevel);
                    return applicantRepository.save(a);
                });

        String objectName = applicant.getApplicantId() + "_" + System.currentTimeMillis() + ".pdf";
        String fileUrl = minioService.uploadCv(cv, objectName);
        ApplicantCv applicantCv = applicantCvRepository.findByApplicant(applicant)
                .orElseGet(ApplicantCv::new);
        applicantCv.setApplicant(applicant);
        applicantCv.setFileUrl(fileUrl);
        applicantCv.setParsedText(null);
        applicantCv.setExtractedSkillsJson(null);
        applicantCvRepository.save(applicantCv);

       JobApplication application = new JobApplication();
// REMOVED: application.setApplicationId(UUID.randomUUID());
application.setApplicant(applicant);
application.setJobPosting(job);
application.setApplicationDate(LocalDate.now());
application.setDesiredSalary(
        desiredSalary != null ? BigDecimal.valueOf(desiredSalary) : null
);
application.setStatus("APPLIED");

JobApplication saved = jobApplicationRepository.save(application); // back to plain save(), works correctly now

return new JobApplicationSubmissionDTO(
        applicant.getApplicantId(),
        saved.getApplicationId(),
        "Candidature reçue. Merci !"
);}
}