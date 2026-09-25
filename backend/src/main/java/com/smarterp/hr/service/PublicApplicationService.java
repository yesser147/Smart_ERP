package com.smarterp.hr.service;

import com.smarterp.hr.domain.*;
import com.smarterp.hr.dto.JobApplicationSubmissionDTO;
import com.smarterp.hr.dto.PublicJobDTO;
import com.smarterp.hr.repository.*;
import com.smarterp.shared.ai.CvAutoProcessor;
import com.smarterp.shared.exception.BadRequestException;
import com.smarterp.shared.exception.ResourceNotFoundException;
import com.smarterp.shared.notification.NotificationService;
import com.smarterp.shared.security.CurrentUser;
import com.smarterp.shared.storage.MinioService;
import com.smarterp.shared.transaction.AfterCommit;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.List;
import java.util.regex.Pattern;

@Service
@RequiredArgsConstructor
public class PublicApplicationService {

    private static final Pattern EMAIL = Pattern.compile("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$");
    private static final long MAX_CV_BYTES = 10L * 1024 * 1024;

    private final ApplicantRepository applicantRepository;
    private final ApplicantCvRepository applicantCvRepository;
    private final JobPostingRepository jobPostingRepository;
    private final JobApplicationRepository jobApplicationRepository;
    private final ApplicationStatusHistoryRepository statusHistoryRepository;
    private final MinioService minioService;
    private final NotificationService notificationService;
    private final CvAutoProcessor cvAutoProcessor;

    @Transactional(readOnly = true)
    public List<PublicJobDTO> openJobs() {
        return jobPostingRepository.findAllWithRelations().stream()
                .filter(p -> "OPEN".equalsIgnoreCase(p.getStatus()))
                .sorted((a, b) -> b.getCreatedAt().compareTo(a.getCreatedAt()))
                .map(PublicJobDTO::fromEntity)
                .toList();
    }

    @Transactional
    public JobApplicationSubmissionDTO submitApplication(
            String firstName, String lastName, String email, String phoneNumber,
            String educationLevel, Long jobId, Double desiredSalary, MultipartFile cv
    ) {
        validate(firstName, lastName, email, cv);
        String cleanEmail = email.trim().toLowerCase();

        JobPosting job = jobPostingRepository.findById(jobId)
                .orElseThrow(() -> new ResourceNotFoundException("No job posting with id " + jobId));
        if (!"OPEN".equalsIgnoreCase(job.getStatus())) {
            throw new BadRequestException("This position is no longer open.");
        }

        Applicant applicant = applicantRepository.findByEmail(cleanEmail).orElseGet(() -> {
            Applicant a = new Applicant();
            a.setFirstName(firstName.trim());
            a.setLastName(lastName.trim());
            a.setEmail(cleanEmail);
            a.setPhoneNumber(phoneNumber);
            a.setEducationLevel(educationLevel);
            return applicantRepository.save(a);
        });

        if (jobApplicationRepository.findByApplicantIdWithRelations(applicant.getApplicantId()).stream()
                .anyMatch(a -> a.getJobPosting().getJobId().equals(jobId))) {
            throw new BadRequestException("You have already applied to this position.");
        }

        String objectName = applicant.getApplicantId() + "_" + System.currentTimeMillis() + ".pdf";
        String fileUrl = minioService.uploadCv(cv, objectName);
        ApplicantCv applicantCv = applicantCvRepository.findByApplicant(applicant).orElseGet(ApplicantCv::new);
        applicantCv.setApplicant(applicant);
        applicantCv.setFileUrl(fileUrl);
        applicantCv.setParsedText(null);            // new CV: must be read again
        applicantCv.setExtractedSkillsJson(null);
        applicantCv.setCvEmbedding(null);
        applicantCvRepository.save(applicantCv);

        JobApplication application = new JobApplication();
        application.setApplicant(applicant);
        application.setJobPosting(job);
        application.setApplicationDate(LocalDate.now());
        application.setDesiredSalary(desiredSalary != null ? BigDecimal.valueOf(desiredSalary) : null);
        application.setStatus("APPLIED");
        JobApplication saved = jobApplicationRepository.save(application);
        statusHistoryRepository.save(new ApplicationStatusHistory(saved.getApplicationId(), null, "APPLIED",
                "SYSTEM".equals(CurrentUser.email()) ? "candidate" : CurrentUser.email()));

        String name = applicant.getFirstName() + " " + applicant.getLastName();
        notificationService.notifyHr("New application",
                name + " applied for " + job.getTitle() + ".", "/dashboard/applicant/" + applicant.getApplicantId());
        Long applicantId = applicant.getApplicantId();
        AfterCommit.run(() -> cvAutoProcessor.process(applicantId, name, job.getTitle()));

        return new JobApplicationSubmissionDTO(applicantId, saved.getApplicationId(),
                "Application received. Thank you!");
    }

    /** The AI engine can only read text PDFs, so anything else is refused up front. */
    private static void validate(String firstName, String lastName, String email, MultipartFile cv) {
        if (firstName == null || firstName.isBlank() || lastName == null || lastName.isBlank()) {
            throw new BadRequestException("First name and last name are required.");
        }
        if (email == null || !EMAIL.matcher(email.trim()).matches()) {
            throw new BadRequestException("Invalid email address.");
        }
        if (cv == null || cv.isEmpty()) {
            throw new BadRequestException("A CV (PDF) is required.");
        }
        if (cv.getSize() > MAX_CV_BYTES) {
            throw new BadRequestException("The CV file is too large (10 MB maximum).");
        }
        String name = cv.getOriginalFilename() == null ? "" : cv.getOriginalFilename().toLowerCase();
        if (!"application/pdf".equalsIgnoreCase(cv.getContentType()) && !name.endsWith(".pdf")) {
            throw new BadRequestException("The CV must be a PDF file.");
        }
        try (InputStream in = cv.getInputStream()) {
            if (!"%PDF-".equals(new String(in.readNBytes(5), StandardCharsets.US_ASCII))) {
                throw new BadRequestException("The file is not a valid PDF.");
            }
        } catch (IOException e) {
            throw new BadRequestException("The CV file could not be read.");
        }
    }
}
