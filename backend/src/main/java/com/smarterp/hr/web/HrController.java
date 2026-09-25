package com.smarterp.hr.web;

import com.smarterp.hr.dto.*;
import com.smarterp.hr.service.HrService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Employees, teams, job postings and the recruitment workflow (HR roles, see SecurityConfig). */
@RestController
@RequestMapping("/hr")
@RequiredArgsConstructor
public class HrController {

    private final HrService hrService;

    // ---------------- teams

    @GetMapping("/departments")
    public List<DepartmentDTO> departments() {
        return hrService.getAllDepartments();
    }

    // ---------------- employees

    @GetMapping("/employees/paged")
    public Page<EmployeeDTO> employees(@RequestParam(defaultValue = "0") int page,
                                       @RequestParam(defaultValue = "25") int size,
                                       @RequestParam(required = false) String search,
                                       @RequestParam(defaultValue = "name") String sortBy,
                                       @RequestParam(defaultValue = "asc") String sortDir) {
        return hrService.getEmployeesPaged(page, size, search, sortBy, sortDir);
    }

    @GetMapping("/employees/{id}")
    public EmployeeDTO employee(@PathVariable Long id) {
        return hrService.getEmployeeById(id);
    }

    @GetMapping("/employees/{id}/salary-history")
    public List<SalaryHistoryDTO> salaryHistory(@PathVariable Long id) {
        return hrService.getSalaryHistoryForEmployee(id);
    }

    @GetMapping("/employees/{id}/trainings")
    public List<EmployeeTrainingDTO> trainings(@PathVariable Long id) {
        return hrService.getTrainingsForEmployee(id);
    }

    @GetMapping("/employees/{id}/surveys")
    public List<EngagementSurveyDTO> surveys(@PathVariable Long id) {
        return hrService.getSurveysForEmployee(id);
    }

    // ---------------- job postings

    @GetMapping("/job-postings")
    public List<JobPostingDTO> jobPostings() {
        return hrService.getAllJobPostings();
    }

    @GetMapping("/job-postings/{id}")
    public JobPostingDTO jobPosting(@PathVariable Long id) {
        return hrService.getJobPosting(id);
    }

    @PostMapping("/job-postings")
    public JobPostingDTO createJobPosting(@Valid @RequestBody JobPostingCreateDTO req) {
        return hrService.createJobPosting(req);
    }

    @PatchMapping("/job-postings/{id}/status")
    public JobPostingDTO updateJobPostingStatus(@PathVariable Long id, @RequestBody Map<String, String> body) {
        return hrService.updateJobPostingStatus(id, body.get("status"));
    }

    @GetMapping("/job-postings/{id}/applications")
    public List<JobApplicationDTO> applicationsForJob(@PathVariable Long id) {
        return hrService.getApplicationsForJob(id);
    }

    // ---------------- applicants & applications

    @GetMapping("/applicants-with-cv-status")
    public List<ApplicantWithCvStatusDTO> applicantsWithCvStatus() {
        return hrService.getAllApplicantsWithCvStatus();
    }

    @GetMapping("/applicants/{id}")
    public ApplicantDTO applicant(@PathVariable Long id) {
        return hrService.getApplicantById(id);
    }

    @GetMapping("/applicants/{id}/applications")
    public List<JobApplicationDTO> applicationsForApplicant(@PathVariable Long id) {
        return hrService.getApplicationsForApplicant(id);
    }

    @GetMapping("/job-applications/{id}/history")
    public List<StatusHistoryDTO> applicationHistory(@PathVariable UUID id) {
        return hrService.getApplicationHistory(id);
    }

    @PatchMapping("/job-applications/{id}/interview")
    public JobApplicationDTO interview(@PathVariable UUID id) {
        return hrService.moveToInterview(id);
    }

    @PatchMapping("/job-applications/{id}/offer")
    public JobApplicationDTO offer(@PathVariable UUID id) {
        return hrService.moveToOffered(id);
    }

    @PatchMapping("/job-applications/{id}/reject")
    public JobApplicationDTO reject(@PathVariable UUID id) {
        return hrService.rejectApplication(id);
    }

    @PostMapping("/applicants/{id}/hire")
    public HireResultDTO hire(@PathVariable Long id, @RequestBody HireRequestDTO request) {
        return hrService.hireApplicant(id, request);
    }
}
