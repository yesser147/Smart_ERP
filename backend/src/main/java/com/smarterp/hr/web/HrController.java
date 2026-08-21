package com.smarterp.hr.web;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

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
import com.smarterp.hr.service.HrService;

import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/hr")
@RequiredArgsConstructor
public class HrController {

    private final HrService hrService;


    // =========================
    // EMPLOYEES
    // =========================

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
    public ResponseEntity<DepartmentDTO> getDepartmentById(
            @PathVariable Long id) {

        return ResponseEntity.ok(hrService.getDepartementById(id));
    }


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
}