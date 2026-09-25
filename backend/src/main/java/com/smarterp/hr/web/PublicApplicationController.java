package com.smarterp.hr.web;

import com.smarterp.hr.dto.JobApplicationSubmissionDTO;
import com.smarterp.hr.dto.PublicJobDTO;
import com.smarterp.hr.service.PublicApplicationService;
import com.smarterp.shared.security.PublicRateLimiter;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

/** Careers site: open to everyone (no login), applications rate-limited per IP. */
@RestController
@RequestMapping("/public")
public class PublicApplicationController {

    private final PublicApplicationService service;
    private final PublicRateLimiter rateLimiter;

    public PublicApplicationController(PublicApplicationService service, PublicRateLimiter rateLimiter) {
        this.service = service;
        this.rateLimiter = rateLimiter;
    }

    @GetMapping("/jobs")
    public List<PublicJobDTO> openJobs() {
        return service.openJobs();
    }

    @PostMapping(value = "/applications", consumes = "multipart/form-data")
    public JobApplicationSubmissionDTO submit(
            HttpServletRequest request,
            @RequestParam String firstName,
            @RequestParam String lastName,
            @RequestParam String email,
            @RequestParam(required = false) String phoneNumber,
            @RequestParam(required = false) String educationLevel,
            @RequestParam Long jobId,
            @RequestParam(required = false) Double desiredSalary,
            @RequestParam MultipartFile cv
    ) {
        rateLimiter.check(request.getRemoteAddr());
        return service.submitApplication(firstName, lastName, email, phoneNumber, educationLevel,
                jobId, desiredSalary, cv);
    }
}
