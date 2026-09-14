package com.smarterp.hr.web;

import com.smarterp.hr.dto.JobApplicationSubmissionDTO;
import com.smarterp.hr.service.PublicApplicationService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/public/applications")
public class PublicApplicationController {

    private final PublicApplicationService service;

    public PublicApplicationController(PublicApplicationService service) {
        this.service = service;
    }

    @PostMapping(consumes = "multipart/form-data")
    public ResponseEntity<JobApplicationSubmissionDTO> submit(
            @RequestParam String firstName,
            @RequestParam String lastName,
            @RequestParam String email,
            @RequestParam(required = false) String phoneNumber,
            @RequestParam(required = false) String educationLevel,
            @RequestParam Long jobId,
            @RequestParam(required = false) Double desiredSalary,
            @RequestParam MultipartFile cv
    ) {
        return ResponseEntity.ok(service.submitApplication(
                firstName, lastName, email, phoneNumber, educationLevel,
                jobId, desiredSalary, cv
        ));
    }
}