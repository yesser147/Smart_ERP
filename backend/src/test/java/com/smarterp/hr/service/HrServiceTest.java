package com.smarterp.hr.service;

import com.smarterp.hr.domain.Applicant;
import com.smarterp.hr.domain.JobApplication;
import com.smarterp.hr.domain.JobPosting;
import com.smarterp.hr.dto.HireRequestDTO;
import com.smarterp.hr.dto.JobPostingCreateDTO;
import com.smarterp.hr.repository.*;
import com.smarterp.security.repository.UserRepository;
import com.smarterp.security.service.AuthService;
import com.smarterp.shared.audit.AuditService;
import com.smarterp.shared.email.EmailService;
import com.smarterp.shared.exception.BadRequestException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class HrServiceTest {

    @Mock DepartmentRepository departmentRepository;
    @Mock EmployeeRepository employeeRepository;
    @Mock SalaryHistoryRepository salaryHistoryRepository;
    @Mock EmployeeTrainingRepository employeeTrainingRepository;
    @Mock EngagementSurveyRepository engagementSurveyRepository;
    @Mock ApplicantRepository applicantRepository;
    @Mock ApplicantCvRepository applicantCvRepository;
    @Mock JobPostingRepository jobPostingRepository;
    @Mock JobApplicationRepository jobApplicationRepository;
    @Mock ApplicationStatusHistoryRepository statusHistoryRepository;
    @Mock UserRepository userRepository;
    @Mock AuthService authService;
    @Mock EmailService emailService;
    @Mock AuditService auditService;

    @InjectMocks HrService service;

    private JobApplication application;
    private final UUID id = UUID.randomUUID();

    @BeforeEach
    void setUp() {
        Applicant applicant = new Applicant();
        applicant.setFirstName("Ada");
        applicant.setLastName("Lovelace");
        applicant.setEmail("ada@example.com");
        JobPosting posting = new JobPosting();
        posting.setTitle("Research Scientist");
        application = new JobApplication();
        application.setApplicationId(id);
        application.setApplicant(applicant);
        application.setJobPosting(posting);
    }

    @Test
    void interviewFromAppliedIsAllowedAndRecorded() {
        application.setStatus("APPLIED");
        when(jobApplicationRepository.findById(id)).thenReturn(Optional.of(application));
        when(jobApplicationRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        var dto = service.moveToInterview(id);

        assertThat(dto.status()).isEqualTo("INTERVIEWING");
        assertThat(application.getStatusUpdatedAt()).isNotNull();
        verify(statusHistoryRepository).save(any());
        verify(auditService).log(eq("APPLICATION_INTERVIEWING"), eq("job_application"), eq(id), any());
    }

    @Test
    void closedApplicationCannotBeRejected() {
        application.setStatus("OFFERED");
        when(jobApplicationRepository.findById(id)).thenReturn(Optional.of(application));

        assertThatThrownBy(() -> service.rejectApplication(id))
                .isInstanceOf(BadRequestException.class)
                .hasMessageContaining("OFFERED");
        verify(jobApplicationRepository, never()).save(any());
    }

    @Test
    void hireRequiresTheMandatoryFields() {
        var incomplete = new HireRequestDTO(null, "Title", null, null, null, null, null,
                LocalDate.now(), BigDecimal.TEN, "ROLE_EMPLOYEE", null);
        assertThatThrownBy(() -> service.hireApplicant(1L, incomplete))
                .isInstanceOf(BadRequestException.class);
    }

    @Test
    void hireRejectsAnUnknownRole() {
        var req = new HireRequestDTO(1L, "Title", null, null, null, null, null,
                LocalDate.now(), BigDecimal.TEN, "ROLE_KING", null);
        assertThatThrownBy(() -> service.hireApplicant(1L, req))
                .isInstanceOf(BadRequestException.class)
                .hasMessageContaining("ROLE_KING");
    }

    @Test
    void jobPostingSalaryRangeMustBeOrdered() {
        var req = new JobPostingCreateDTO("Analyst", 1L, null, BigDecimal.ONE,
                BigDecimal.valueOf(90000), BigDecimal.valueOf(50000), null);
        assertThatThrownBy(() -> service.createJobPosting(req))
                .isInstanceOf(BadRequestException.class);
        verifyNoInteractions(jobPostingRepository);
    }
}
