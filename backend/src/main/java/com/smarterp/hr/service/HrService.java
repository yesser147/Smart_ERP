package com.smarterp.hr.service;


import com.smarterp.hr.domain.Applicant;
import com.smarterp.hr.domain.ApplicantCv;
import com.smarterp.hr.domain.Department;
import com.smarterp.hr.domain.JobApplication;
import com.smarterp.hr.domain.JobPosting;
import com.smarterp.hr.dto.*;
import com.smarterp.hr.repository.*;
import com.smarterp.shared.email.EmailService;
import com.smarterp.shared.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import com.smarterp.shared.storage.MinioService;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class HrService {

    private final DepartmentRepository departmentRepository;
    private final EmployeeRepository employeeRepository;
    private final SalaryHistoryRepository salaryHistoryRepository;
    private final TrainingCourseRepository trainingCourseRepository;
    private final EmployeeTrainingRepository employeeTrainingRepository;
    private final EngagementSurveyRepository engagementSurveyRepository;
    private final ApplicantRepository applicantRepository;
    private final JobPostingRepository jobPostingRepository;
    private final JobApplicationRepository jobApplicationRepository;
    private final ApplicantCvRepository applicantCvRepository;
    private final EmailService emailService;
    private final JdbcTemplate jdbcTemplate;
    private final MinioService minioService;

    public List<DepartmentDTO> getAllDepartments() {
        return departmentRepository.findAll()
                .stream()
                .map(DepartmentDTO::fromEntity)
                .collect(Collectors.toList());
    }

    public DepartmentDTO getDepartementById(Long id) {
        Department department = departmentRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Aucun Departement trouvé avec l'id : " + id));
        return DepartmentDTO.fromEntity(department);
    }

    @Transactional(readOnly = true)
    public List<EmployeeDTO> getAllEmployees() {
        return employeeRepository.findAllWithRelations().stream()
                .map(EmployeeDTO::fromEntity)
                .toList();
    }

    public List<SalaryHistoryDTO> getAllSalaryHistory() {
        return salaryHistoryRepository.findAll()
                .stream()
                .map(SalaryHistoryDTO::fromEntity)
                .collect(Collectors.toList());
    }

    public List<TrainingCourseDTO> getAllTrainingCourses() {
        return trainingCourseRepository.findAll()
                .stream()
                .map(TrainingCourseDTO::fromEntity)
                .collect(Collectors.toList());
    }

    public List<EmployeeTrainingDTO> getAllEmployeeTrainings() {
        return employeeTrainingRepository.findAll()
                .stream()
                .map(EmployeeTrainingDTO::fromEntity)
                .collect(Collectors.toList());
    }

    public List<EngagementSurveyDTO> getAllEngagementSurveys() {
        return engagementSurveyRepository.findAll()
                .stream()
                .map(EngagementSurveyDTO::fromEntity)
                .collect(Collectors.toList());
    }

    public List<ApplicantDTO> getAllApplicants() {
        return applicantRepository.findAll()
                .stream()
                .map(ApplicantDTO::fromEntity)
                .collect(Collectors.toList());
    }

    public List<JobPostingDTO> getAllJobPostings() {
        return jobPostingRepository.findAllWithRelations()
                .stream()
                .map(JobPostingDTO::fromEntity)
                .collect(Collectors.toList());
    }

public List<JobApplicationDTO> getAllJobApplications() {
    return jobApplicationRepository.findAllWithRelations()
            .stream()
            .map(JobApplicationDTO::fromEntity)
            .collect(Collectors.toList());
}

    public List<ApplicantCvDTO> getAllApplicantCvs() {
        return applicantCvRepository.findAll()
                .stream()
                .map(ApplicantCvDTO::fromEntity)
                .collect(Collectors.toList());
    }

    // =========================
    // APPLICATION STATUS ACTIONS (interview / offer / reject)
    // =========================

    @Transactional
    public JobApplicationDTO moveToInterview(UUID applicationId) {
        JobApplication application = jobApplicationRepository.findById(applicationId)
                .orElseThrow(() -> new ResourceNotFoundException("Aucune candidature trouvée avec l'id : " + applicationId));

        application.setStatus("INTERVIEWING");
        JobApplication saved = jobApplicationRepository.save(application);

        emailService.sendInterviewInvitationEmail(
                saved.getApplicant().getEmail(),
                saved.getApplicant().getFirstName() + " " + saved.getApplicant().getLastName(),
                saved.getJobPosting().getTitle()
        );

        return JobApplicationDTO.fromEntity(saved);
    }

    @Transactional
    public JobApplicationDTO moveToOffered(UUID applicationId) {
        JobApplication application = jobApplicationRepository.findById(applicationId)
                .orElseThrow(() -> new ResourceNotFoundException("Aucune candidature trouvée avec l'id : " + applicationId));

        application.setStatus("OFFERED");
        JobApplication saved = jobApplicationRepository.save(application);

        emailService.sendOfferEmail(
                saved.getApplicant().getEmail(),
                saved.getApplicant().getFirstName() + " " + saved.getApplicant().getLastName(),
                saved.getJobPosting().getTitle()
        );

        return JobApplicationDTO.fromEntity(saved);
    }

    @Transactional
    public JobApplicationDTO rejectApplication(UUID applicationId) {
        JobApplication application = jobApplicationRepository.findById(applicationId)
                .orElseThrow(() -> new ResourceNotFoundException("Aucune candidature trouvée avec l'id : " + applicationId));

        application.setStatus("REJECTED");
        JobApplication saved = jobApplicationRepository.save(application);

        emailService.sendRejectionEmail(
                saved.getApplicant().getEmail(),
                saved.getApplicant().getFirstName() + " " + saved.getApplicant().getLastName(),
                saved.getJobPosting().getTitle()
        );

        return JobApplicationDTO.fromEntity(saved);
    }

    public ApplicantDTO getApplicantById(Long id) {
        Applicant applicant = applicantRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Aucun candidat trouvé avec l'id : " + id));
        return ApplicantDTO.fromEntity(applicant);
    }

    /**
     * Converts an applicant into a real employee + login account.
     * Uses JdbcTemplate for the employee/user inserts (not JPA entities)
     * since employees.employee_id is a plain BIGINT seeded by the ETL --
     * see the schema.sql sequence addition this relies on. Reuses the
     * applicant's own name/gender/dob rather than asking HR to retype
     * data already on file.
     */
    @Transactional
    public HireResultDTO hireApplicant(Long applicantId, HireRequestDTO req) {
        Applicant applicant = applicantRepository.findById(applicantId)
                .orElseThrow(() -> new ResourceNotFoundException("Aucun candidat trouvé avec l'id : " + applicantId));

        if (!departmentRepository.existsById(req.departmentId())) {
            throw new ResourceNotFoundException("Aucun département trouvé avec l'id : " + req.departmentId());
        }

        Long employeeId = jdbcTemplate.queryForObject("""
            INSERT INTO employees
                (department_id, first_name, last_name, start_date, title,
                 employee_status, employee_type, employee_classification_type,
                 dob, state, job_function, gender, location, salary, currency,
                 is_deleted, needs_review, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'Active', ?, ?, ?, ?, ?, ?, ?, ?, 'USD',
                    FALSE, FALSE, now(), now())
            RETURNING employee_id
            """,
            Long.class,
            req.departmentId(), applicant.getFirstName(), applicant.getLastName(),
            req.startDate(), req.title(), req.employeeType(), req.employeeClassificationType(),
            applicant.getDob(), req.state(), req.jobFunction(), applicant.getGender(),
            req.location(), req.salary()
        );

        jdbcTemplate.update("""
            INSERT INTO salary_history (employee_id, effective_date, salary, currency, change_reason, created_at)
            VALUES (?, ?, ?, 'USD', 'INITIAL_HIRE', now())
            """,
            employeeId, req.startDate(), req.salary()
        );

        Long roleId = jdbcTemplate.queryForObject(
            "SELECT id FROM roles WHERE name = ?", Long.class, req.roleName()
        );

        UUID userId = UUID.randomUUID();
        jdbcTemplate.update("""
            INSERT INTO users (id, employee_id, email, password_hash, is_active, role_id, created_at, updated_at, created_by, updated_by)
            VALUES (?, ?, ?, NULL, FALSE, ?, now(), now(), 'HIRE_FLOW', 'HIRE_FLOW')
            """,
            userId, employeeId, applicant.getEmail(), roleId
        );

        UUID tokenId = UUID.randomUUID();
        String token = UUID.randomUUID().toString();
        LocalDateTime expiresAt = LocalDateTime.now().plusDays(7);
        jdbcTemplate.update("""
            INSERT INTO user_tokens (id, user_id, token, token_type, expires_at, is_used, is_revoked, created_at)
            VALUES (?, ?, ?, 'ACTIVATION', ?, FALSE, FALSE, now())
            """,
            tokenId, userId, token, expiresAt
        );

        // TODO: point this at your real frontend activation route.
        String activationUrl = "http://localhost:4200/activate?token=" + token;
        boolean emailSent = true;
        try {
            emailService.sendAccountActivationEmail(applicant.getEmail(), req.roleName(), activationUrl);
        } catch (Exception e) {
            emailSent = false;
        }

        if (req.jobApplicationId() != null) {
            jobApplicationRepository.findById(req.jobApplicationId()).ifPresent(app -> {
                app.setStatus("OFFERED");
                jobApplicationRepository.save(app);
            });
        }

        return new HireResultDTO(employeeId, applicant.getEmail(), emailSent);
    }

    
    
    public EmployeeDTO getEmployeeById(Long id) {
    return employeeRepository.findById(id)
            .map(EmployeeDTO::fromEntity)
            .orElseThrow(() -> new ResourceNotFoundException("Aucun employé trouvé avec l'id : " + id));
}
public List<ApplicantWithCvStatusDTO> getAllApplicantsWithCvStatus() {
    var applicants = applicantRepository.findAll();

    var statusByApplicantId = applicantCvRepository.findAllCvStatus().stream()
            .collect(Collectors.toMap(
                    ApplicantCvStatusView::applicantId,
                    java.util.function.Function.identity()
            ));

    return applicants.stream()
            .map(a -> {
                var status = statusByApplicantId.get(a.getApplicantId());
                boolean hasCv = status != null && status.hasCv();
                boolean isProcessed = status != null && status.isProcessed();
                return new ApplicantWithCvStatusDTO(
                        a.getApplicantId(), a.getFirstName(), a.getLastName(), a.getEmail(),
                        a.getEducationLevel(), a.getYearsOfExperience(), hasCv, isProcessed,
                        a.getCreatedAt()
                );
            })
            .collect(Collectors.toList());
}
}