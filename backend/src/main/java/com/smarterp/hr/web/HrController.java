package com.smarterp.hr.web;

import com.smarterp.hr.dto.ApplicantCvDTO;
import com.smarterp.hr.dto.ApplicantDTO;
import com.smarterp.hr.dto.ApplicantWithCvStatusDTO;
import com.smarterp.hr.dto.DepartmentDTO;
import com.smarterp.hr.dto.EmployeeDTO;
import com.smarterp.hr.dto.EmployeeTrainingDTO;
import com.smarterp.hr.dto.EngagementSurveyDTO;
import com.smarterp.hr.dto.HireRequestDTO;
import com.smarterp.hr.dto.HireResultDTO;
import com.smarterp.hr.dto.JobApplicationDTO;
import com.smarterp.hr.dto.JobPostingDTO;
import com.smarterp.hr.dto.SalaryHistoryDTO;
import com.smarterp.hr.dto.TrainingCourseDTO;
import com.smarterp.hr.service.HrService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/hr")
@RequiredArgsConstructor
public class HrController {

    private final HrService hrService;

    @GetMapping("/employees")
    public ResponseEntity<List<EmployeeDTO>> getAllEmployees() {
        return ResponseEntity.ok(hrService.getAllEmployees());
    }
    // =========================
    // DEPARTMENTS
    // =========================

    @GetMapping("/departments")
    public ResponseEntity<List<DepartmentDTO>> getAllDepartments() {
        return ResponseEntity.ok(hrService.getAllDepartments());
    }

    @GetMapping("/departments/{id}")
    public ResponseEntity<DepartmentDTO> getDepartmentById(@PathVariable Long id) {
        return ResponseEntity.ok(hrService.getDepartementById(id));
    }

    // =========================
    // SALARY & TRAINING
    // =========================

    @GetMapping("/salary-history")
    public ResponseEntity<List<SalaryHistoryDTO>> getAllSalaryHistory() {
        return ResponseEntity.ok(hrService.getAllSalaryHistory());
    }

    @GetMapping("/training-courses")
    public ResponseEntity<List<TrainingCourseDTO>> getAllTrainingCourses() {
        return ResponseEntity.ok(hrService.getAllTrainingCourses());
    }

    @GetMapping("/employee-trainings")
    public ResponseEntity<List<EmployeeTrainingDTO>> getAllEmployeeTrainings() {
        return ResponseEntity.ok(hrService.getAllEmployeeTrainings());
    }

    // =========================
    // ENGAGEMENT & RECRUITMENT
    // =========================

    @GetMapping("/engagement-surveys")
    public ResponseEntity<List<EngagementSurveyDTO>> getAllEngagementSurveys() {
        return ResponseEntity.ok(hrService.getAllEngagementSurveys());
    }

    @GetMapping("/applicants")
    public ResponseEntity<List<ApplicantDTO>> getAllApplicants() {
        return ResponseEntity.ok(hrService.getAllApplicants());
    }

    @GetMapping("/job-postings")
    public ResponseEntity<List<JobPostingDTO>> getAllJobPostings() {
        return ResponseEntity.ok(hrService.getAllJobPostings());
    }

    @GetMapping("/job-applications")
    public ResponseEntity<List<JobApplicationDTO>> getAllJobApplications() {
        return ResponseEntity.ok(hrService.getAllJobApplications());
    }

    @GetMapping("/applicant-cvs")
    public ResponseEntity<List<ApplicantCvDTO>> getAllApplicantCvs() {
        return ResponseEntity.ok(hrService.getAllApplicantCvs());
    }

    // =========================
    // APPLICATION STATUS ACTIONS
    // =========================

    @PatchMapping("/job-applications/{id}/interview")
    public ResponseEntity<JobApplicationDTO> moveToInterview(@PathVariable UUID id) {
        return ResponseEntity.ok(hrService.moveToInterview(id));
    }

    @PatchMapping("/job-applications/{id}/offer")
    public ResponseEntity<JobApplicationDTO> moveToOffered(@PathVariable UUID id) {
        return ResponseEntity.ok(hrService.moveToOffered(id));
    }

    @PatchMapping("/job-applications/{id}/reject")
    public ResponseEntity<JobApplicationDTO> rejectApplication(@PathVariable UUID id) {
        return ResponseEntity.ok(hrService.rejectApplication(id));
    }
    @GetMapping("/applicants/{id}")
public ResponseEntity<ApplicantDTO> getApplicantById(@PathVariable Long id) {
    return ResponseEntity.ok(hrService.getApplicantById(id));
}

@PostMapping("/applicants/{id}/hire")
public ResponseEntity<HireResultDTO> hireApplicant(@PathVariable Long id, @RequestBody HireRequestDTO request) {
    return ResponseEntity.ok(hrService.hireApplicant(id, request));
}
@GetMapping("/applicants-with-cv-status")
public ResponseEntity<List<ApplicantWithCvStatusDTO>> getApplicantsWithCvStatus() {
    return ResponseEntity.ok(hrService.getAllApplicantsWithCvStatus());
}
}