package com.smarterp.hr.service;

import com.smarterp.hr.domain.*;
import com.smarterp.hr.dto.*;
import com.smarterp.hr.repository.*;
import com.smarterp.security.domain.RoleName;
import com.smarterp.security.domain.User;
import com.smarterp.security.dto.AuthResponse;
import com.smarterp.security.dto.RegisterRequest;
import com.smarterp.security.repository.UserRepository;
import com.smarterp.security.service.AuthService;
import com.smarterp.shared.audit.AuditService;
import com.smarterp.shared.email.EmailService;
import com.smarterp.shared.exception.BadRequestException;
import com.smarterp.shared.exception.ResourceNotFoundException;
import com.smarterp.shared.security.CurrentUser;
import com.smarterp.shared.transaction.AfterCommit;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;

/** Employees, departments, job postings and the recruitment workflow. */
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class HrService {

    // A hired (OFFERED) or REJECTED application is closed.
    private static final Set<String> CAN_INTERVIEW = Set.of("APPLIED", "IN REVIEW");
    private static final Set<String> CAN_OFFER = Set.of("APPLIED", "IN REVIEW", "INTERVIEWING");
    private static final Set<String> CAN_REJECT = Set.of("APPLIED", "IN REVIEW", "INTERVIEWING");
    private static final Set<String> POSTING_STATUSES = Set.of("OPEN", "CLOSED", "FILLED");

    private final DepartmentRepository departmentRepository;
    private final EmployeeRepository employeeRepository;
    private final SalaryHistoryRepository salaryHistoryRepository;
    private final EmployeeTrainingRepository employeeTrainingRepository;
    private final EngagementSurveyRepository engagementSurveyRepository;
    private final ApplicantRepository applicantRepository;
    private final ApplicantCvRepository applicantCvRepository;
    private final JobPostingRepository jobPostingRepository;
    private final JobApplicationRepository jobApplicationRepository;
    private final ApplicationStatusHistoryRepository statusHistoryRepository;
    private final UserRepository userRepository;
    private final AuthService authService;
    private final EmailService emailService;
    private final AuditService auditService;

    // =========================
    // DEPARTMENTS (teams)
    // =========================

    public List<DepartmentDTO> getAllDepartments() {
        return departmentRepository.findAll().stream().map(DepartmentDTO::fromEntity).toList();
    }

    // =========================
    // EMPLOYEES
    // =========================

    public Page<EmployeeDTO> getEmployeesPaged(int page, int size, String search, String sortBy, String sortDir) {
        Sort sort = Sort.by("desc".equalsIgnoreCase(sortDir) ? Sort.Direction.DESC : Sort.Direction.ASC,
                mapSortColumn(sortBy));
        return employeeRepository.findPageWithSearch(search, PageRequest.of(page, Math.min(size, 200), sort))
                .map(EmployeeDTO::fromEntity);
    }

    private static String mapSortColumn(String sortBy) {
        return switch (sortBy == null ? "" : sortBy) {
            case "title" -> "title";
            case "employeeStatus" -> "employeeStatus";
            case "salary" -> "salary";
            case "startDate" -> "startDate";
            default -> "lastName";
        };
    }

    public EmployeeDTO getEmployeeById(Long id) {
        return employeeRepository.findById(id)
                .map(EmployeeDTO::fromEntity)
                .orElseThrow(() -> new ResourceNotFoundException("No employee with id " + id));
    }

    public List<SalaryHistoryDTO> getSalaryHistoryForEmployee(Long employeeId) {
        return salaryHistoryRepository.findByEmployeeEmployeeIdOrderByEffectiveDateDesc(employeeId)
                .stream().map(SalaryHistoryDTO::fromEntity).toList();
    }

    public List<EmployeeTrainingDTO> getTrainingsForEmployee(Long employeeId) {
        return employeeTrainingRepository.findByEmployeeEmployeeIdOrderByTrainingDateDesc(employeeId)
                .stream().map(EmployeeTrainingDTO::fromEntity).toList();
    }

    public List<EngagementSurveyDTO> getSurveysForEmployee(Long employeeId) {
        return engagementSurveyRepository.findByEmployeeEmployeeIdOrderBySurveyDateDesc(employeeId)
                .stream().map(EngagementSurveyDTO::fromEntity).toList();
    }

    // =========================
    // JOB POSTINGS
    // =========================

    public List<JobPostingDTO> getAllJobPostings() {
        Map<Long, Long> counts = jobApplicationRepository.countByJob().stream()
                .collect(Collectors.toMap(r -> (Long) r[0], r -> (Long) r[1]));
        return jobPostingRepository.findAllWithRelations().stream()
                .map(p -> JobPostingDTO.fromEntity(p, counts.getOrDefault(p.getJobId(), 0L).intValue()))
                .toList();
    }

    public JobPostingDTO getJobPosting(Long jobId) {
        JobPosting posting = findPosting(jobId);
        return JobPostingDTO.fromEntity(posting, jobApplicationRepository.countByJobPostingJobId(jobId).intValue());
    }

    @Transactional
    public JobPostingDTO createJobPosting(JobPostingCreateDTO req) {
        if (req.offeredSalaryMin() != null && req.offeredSalaryMax() != null
                && req.offeredSalaryMin().compareTo(req.offeredSalaryMax()) > 0) {
            throw new BadRequestException("The minimum salary is higher than the maximum salary.");
        }
        Department team = departmentRepository.findById(req.departmentId())
                .orElseThrow(() -> new ResourceNotFoundException("No team with id " + req.departmentId()));

        JobPosting posting = new JobPosting();
        posting.setTitle(req.title().trim());
        posting.setDepartment(team);
        posting.setLocation(req.location() == null || req.location().isBlank() ? "Head Office" : req.location());
        posting.setRequiredExperienceYears(req.requiredExperienceYears());
        posting.setOfferedSalaryMin(req.offeredSalaryMin());
        posting.setOfferedSalaryMax(req.offeredSalaryMax());
        posting.setDescription(req.description());
        posting.setStatus("OPEN");
        JobPosting saved = jobPostingRepository.save(posting);

        auditService.log("JOB_POSTING_CREATED", "job_posting", saved.getJobId(), saved.getTitle());
        return JobPostingDTO.fromEntity(saved, 0);
    }

    @Transactional
    public JobPostingDTO updateJobPostingStatus(Long jobId, String status) {
        String newStatus = status == null ? "" : status.toUpperCase();
        if (!POSTING_STATUSES.contains(newStatus)) {
            throw new BadRequestException("Unknown posting status: " + status);
        }
        JobPosting posting = findPosting(jobId);
        String old = posting.getStatus();
        posting.setStatus(newStatus);
        auditService.log("JOB_POSTING_STATUS", "job_posting", jobId, old + " -> " + newStatus);
        return getJobPosting(jobId);
    }

    private JobPosting findPosting(Long jobId) {
        return jobPostingRepository.findById(jobId)
                .orElseThrow(() -> new ResourceNotFoundException("No job posting with id " + jobId));
    }

    // =========================
    // APPLICANTS & APPLICATIONS
    // =========================

    public ApplicantDTO getApplicantById(Long id) {
        return applicantRepository.findById(id)
                .map(ApplicantDTO::fromEntity)
                .orElseThrow(() -> new ResourceNotFoundException("No applicant with id " + id));
    }

    public List<ApplicantWithCvStatusDTO> getAllApplicantsWithCvStatus() {
        var statusByApplicant = applicantCvRepository.findAllCvStatus().stream()
                .collect(Collectors.toMap(ApplicantCvStatusView::applicantId, Function.identity()));
        return applicantRepository.findAll().stream()
                .map(a -> {
                    var status = statusByApplicant.get(a.getApplicantId());
                    return new ApplicantWithCvStatusDTO(
                            a.getApplicantId(), a.getFirstName(), a.getLastName(), a.getEmail(),
                            a.getEducationLevel(), a.getYearsOfExperience(),
                            status != null && status.hasCv(), status != null && status.isProcessed(),
                            a.getCreatedAt());
                })
                .toList();
    }

    public List<JobApplicationDTO> getApplicationsForJob(Long jobId) {
        return jobApplicationRepository.findByJobIdWithRelations(jobId)
                .stream().map(JobApplicationDTO::fromEntity).toList();
    }

    public List<JobApplicationDTO> getApplicationsForApplicant(Long applicantId) {
        return jobApplicationRepository.findByApplicantIdWithRelations(applicantId)
                .stream().map(JobApplicationDTO::fromEntity).toList();
    }

    public List<StatusHistoryDTO> getApplicationHistory(UUID applicationId) {
        return statusHistoryRepository.findByApplicationIdOrderByChangedAtAsc(applicationId)
                .stream().map(StatusHistoryDTO::fromEntity).toList();
    }

    private JobApplication changeStatus(UUID applicationId, Set<String> allowedFrom, String newStatus) {
        JobApplication application = jobApplicationRepository.findById(applicationId)
                .orElseThrow(() -> new ResourceNotFoundException("No application with id " + applicationId));

        String current = application.getStatus() == null ? "" : application.getStatus().toUpperCase();
        if (!allowedFrom.contains(current)) {
            throw new BadRequestException("An application cannot go from " + current + " to " + newStatus + ".");
        }
        recordStatus(application, newStatus);
        return jobApplicationRepository.save(application);
    }

    /** Sets the status, dates it, and keeps the history + audit trail. */
    private void recordStatus(JobApplication application, String newStatus) {
        String old = application.getStatus();
        application.setStatus(newStatus);
        application.setStatusUpdatedAt(LocalDateTime.now());
        statusHistoryRepository.save(new ApplicationStatusHistory(
                application.getApplicationId(), old, newStatus, CurrentUser.email()));
        auditService.log("APPLICATION_" + newStatus.replace(' ', '_'), "job_application",
                application.getApplicationId(),
                applicantName(application) + " / " + application.getJobPosting().getTitle());
    }

    private static String applicantName(JobApplication application) {
        return application.getApplicant().getFirstName() + " " + application.getApplicant().getLastName();
    }

    @Transactional
    public JobApplicationDTO moveToInterview(UUID applicationId) {
        JobApplication saved = changeStatus(applicationId, CAN_INTERVIEW, "INTERVIEWING");
        String email = saved.getApplicant().getEmail(), name = applicantName(saved), job = saved.getJobPosting().getTitle();
        AfterCommit.run(() -> emailService.sendInterviewInvitationEmail(email, name, job));
        return JobApplicationDTO.fromEntity(saved);
    }

    @Transactional
    public JobApplicationDTO moveToOffered(UUID applicationId) {
        JobApplication saved = changeStatus(applicationId, CAN_OFFER, "OFFERED");
        String email = saved.getApplicant().getEmail(), name = applicantName(saved), job = saved.getJobPosting().getTitle();
        AfterCommit.run(() -> emailService.sendOfferEmail(email, name, job));
        return JobApplicationDTO.fromEntity(saved);
    }

    @Transactional
    public JobApplicationDTO rejectApplication(UUID applicationId) {
        JobApplication saved = changeStatus(applicationId, CAN_REJECT, "REJECTED");
        String email = saved.getApplicant().getEmail(), name = applicantName(saved), job = saved.getJobPosting().getTitle();
        AfterCommit.run(() -> emailService.sendRejectionEmail(email, name, job));
        return JobApplicationDTO.fromEntity(saved);
    }

    // =========================
    // HIRING
    // =========================

    @Transactional
    public HireResultDTO hireApplicant(Long applicantId, HireRequestDTO req) {
        if (req == null || req.departmentId() == null || req.startDate() == null || req.salary() == null
                || req.title() == null || req.title().isBlank() || req.roleName() == null) {
            throw new BadRequestException("Team, title, start date, salary and role are required.");
        }
        RoleName roleName;
        try {
            roleName = RoleName.valueOf(req.roleName());
        } catch (IllegalArgumentException e) {
            throw new BadRequestException("Unknown role: " + req.roleName());
        }

        Applicant applicant = applicantRepository.findById(applicantId)
                .orElseThrow(() -> new ResourceNotFoundException("No applicant with id " + applicantId));

        // One login per email: an existing account means this person was already hired
        if (Boolean.TRUE.equals(userRepository.existsByEmail(applicant.getEmail()))) {
            throw new BadRequestException("An account already exists for " + applicant.getEmail()
                    + ": this candidate has already been hired.");
        }

        Department team = departmentRepository.findById(req.departmentId())
                .orElseThrow(() -> new ResourceNotFoundException("No team with id " + req.departmentId()));

        // 1. The employee, reusing what the applicant already gave us
        Employee employee = new Employee();
        employee.setDepartment(team);
        employee.setFirstName(applicant.getFirstName());
        employee.setLastName(applicant.getLastName());
        employee.setStartDate(req.startDate());
        employee.setTitle(req.title());
        employee.setEmployeeStatus("Active");
        employee.setEmployeeType(req.employeeType());
        employee.setEmployeeClassificationType(req.employeeClassificationType());
        employee.setDob(applicant.getDob());
        employee.setState(req.state());
        employee.setJobFunction(req.jobFunction());
        employee.setGender(applicant.getGender());
        employee.setLocation(req.location());
        employee.setSalary(req.salary());
        employee.setCurrency("USD");
        Employee saved = employeeRepository.save(employee);

        // 2. Initial salary history row
        SalaryHistory history = new SalaryHistory();
        history.setEmployee(saved);
        history.setEffectiveDate(req.startDate());
        history.setSalary(req.salary());
        history.setCurrency("USD");
        history.setChangeReason("INITIAL_HIRE");
        salaryHistoryRepository.save(history);

        // 3. Login account (role, temporary password, activation token and email)
        AuthResponse account = authService.register(new RegisterRequest(
                applicant.getEmail(), UUID.randomUUID().toString(), roleName));
        User user = userRepository.findById(account.userId())
                .orElseThrow(() -> new ResourceNotFoundException("User not found after creation."));
        user.setEmployeeId(saved.getEmployeeId());

        // 4. The application is OFFERED and the posting FILLED
        if (req.jobApplicationId() != null) {
            jobApplicationRepository.findById(req.jobApplicationId()).ifPresent(app -> {
                if (!"OFFERED".equalsIgnoreCase(app.getStatus())) {
                    recordStatus(app, "OFFERED");
                }
                app.getJobPosting().setStatus("FILLED");
            });
        }

        auditService.log("EMPLOYEE_HIRED", "employee", saved.getEmployeeId(),
                applicant.getFirstName() + " " + applicant.getLastName() + " as " + req.title());
        return new HireResultDTO(saved.getEmployeeId(), applicant.getEmail(), true);
    }
}
