package com.smarterp.hr.service;

import com.smarterp.hr.domain.Department;
import com.smarterp.hr.domain.JobApplication;
import com.smarterp.hr.dto.ApplicantCvDTO;
import com.smarterp.hr.dto.ApplicantDTO;
import com.smarterp.hr.dto.DepartmentDTO;
import com.smarterp.hr.dto.EmployeeDTO;
import com.smarterp.hr.dto.EmployeeTrainingDTO;
import com.smarterp.hr.dto.EngagementSurveyDTO;
import com.smarterp.hr.dto.JobApplicationDTO;
import com.smarterp.hr.dto.JobPostingDTO;
import com.smarterp.hr.dto.SalaryHistoryDTO;
import com.smarterp.hr.dto.TrainingCourseDTO;
import com.smarterp.hr.repository.ApplicantCvRepository;
import com.smarterp.hr.repository.ApplicantRepository;
import com.smarterp.hr.repository.DepartmentRepository;
import com.smarterp.hr.repository.EmployeeRepository;
import com.smarterp.hr.repository.EmployeeTrainingRepository;
import com.smarterp.hr.repository.EngagementSurveyRepository;
import com.smarterp.hr.repository.JobApplicationRepository;
import com.smarterp.hr.repository.JobPostingRepository;
import com.smarterp.hr.repository.SalaryHistoryRepository;
import com.smarterp.hr.repository.TrainingCourseRepository;
import com.smarterp.shared.email.EmailService;
import com.smarterp.shared.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

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
        return jobApplicationRepository.findAll()
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
}