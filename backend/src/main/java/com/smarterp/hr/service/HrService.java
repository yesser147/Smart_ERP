package com.smarterp.hr.service;


import com.smarterp.hr.domain.Applicant;
import com.smarterp.hr.domain.ApplicantCv;
import com.smarterp.hr.domain.Department;
import com.smarterp.hr.domain.Employee;
import com.smarterp.hr.domain.JobApplication;
import com.smarterp.hr.domain.JobPosting;
import com.smarterp.hr.domain.SalaryHistory;
import com.smarterp.hr.dto.*;
import com.smarterp.hr.repository.*;
import com.smarterp.security.domain.RoleName;
import com.smarterp.security.domain.User;
import com.smarterp.security.dto.AuthResponse;
import com.smarterp.security.dto.RegisterRequest;
import com.smarterp.security.repository.UserRepository;
import com.smarterp.security.service.AuthService;
import com.smarterp.shared.email.EmailService;
import com.smarterp.shared.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import com.smarterp.shared.storage.MinioService;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;

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
    private final AuthService authService;
    private final UserRepository userRepository;

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

public Page<EmployeeDTO> getEmployeesPaged(int page, int size, String search, String sortBy, String sortDir) {
    Sort sort = Sort.by(sortDir.equalsIgnoreCase("desc") ? Sort.Direction.DESC : Sort.Direction.ASC,
                         mapSortColumn(sortBy));
    Pageable pageable = PageRequest.of(page, size, sort);

    return employeeRepository.findPageWithSearch(search, pageable)
            .map(EmployeeDTO::fromEntity);
}

private String mapSortColumn(String sortBy) {
    return switch (sortBy) {
        case "name" -> "lastName";
        case "title" -> "title";
        case "employeeStatus" -> "employeeStatus";
        case "salary" -> "salary";
        case "startDate" -> "startDate";
        default -> "lastName";
    };
}
    @Transactional
public HireResultDTO hireApplicant(Long applicantId, HireRequestDTO req) {
    Applicant applicant = applicantRepository.findById(applicantId)
            .orElseThrow(() -> new ResourceNotFoundException("Aucun candidat trouvé avec l'id : " + applicantId));

    Department department = departmentRepository.findById(req.departmentId())
            .orElseThrow(() -> new ResourceNotFoundException("Aucun département trouvé avec l'id : " + req.departmentId()));

    // 1. Create the real Employee record, reusing what the applicant
    // already gave us (name, gender, dob) instead of asking HR to retype it.
    Employee employee = new Employee();
    employee.setDepartment(department);
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
    Employee savedEmployee = employeeRepository.save(employee);

    // employee_id is a plain BIGINT with no @GeneratedValue in this
    // entity -- confirm the employees_employee_id_seq DEFAULT from the
    // earlier schema.sql fix is in place, or this insert will fail
    // needing an explicit ID.

    // 2. Initial salary history row, same as any other new hire.
    SalaryHistory salaryHistory = new SalaryHistory();
    salaryHistory.setEmployee(savedEmployee);
    salaryHistory.setEffectiveDate(req.startDate());
    salaryHistory.setSalary(req.salary());
    salaryHistory.setCurrency("USD");
    salaryHistory.setChangeReason("INITIAL_HIRE");
    salaryHistoryRepository.save(salaryHistory);

    // 3. Real login account, reusing AuthService's actual registration
    // logic (role lookup, password hashing, activation token, email)
    // instead of duplicating it with raw JDBC inserts.
    RegisterRequest registerRequest = new RegisterRequest(
            applicant.getEmail(),
            UUID.randomUUID().toString(), // temporary password; user sets a real one via the activation link
            RoleName.valueOf(req.roleName())
    );
    AuthResponse authResponse = authService.register(registerRequest);
    User user = userRepository.findById(authResponse.userId())
            .orElseThrow(() -> new ResourceNotFoundException("Utilisateur introuvable après création."));
    user.setEmployeeId(savedEmployee.getEmployeeId());
    userRepository.save(user);

    // 4. Mark the application OFFERED and close the job posting so it
    // stops accepting new applications / showing as open.
    if (req.jobApplicationId() != null) {
        jobApplicationRepository.findById(req.jobApplicationId()).ifPresent(app -> {
            app.setStatus("OFFERED");
            JobApplication savedApp = jobApplicationRepository.save(app);

            JobPosting posting = savedApp.getJobPosting();
            posting.setStatus("FILLED");
            jobPostingRepository.save(posting);
        });
    }

    return new HireResultDTO(savedEmployee.getEmployeeId(), applicant.getEmail(), true);
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