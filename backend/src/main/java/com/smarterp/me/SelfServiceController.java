package com.smarterp.me;

import com.smarterp.hr.dto.*;
import com.smarterp.hr.service.HrService;
import com.smarterp.hr.service.LeaveService;
import com.smarterp.hr.service.WorkforceService;
import com.smarterp.security.repository.UserRepository;
import com.smarterp.shared.exception.BadRequestException;
import com.smarterp.shared.security.SecurityUser;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/** Employee self-service: every logged-in employee sees only their own file. */
@RestController
@RequestMapping("/me")
@RequiredArgsConstructor
public class SelfServiceController {

    private final UserRepository userRepository;
    private final HrService hrService;
    private final WorkforceService workforceService;
    private final LeaveService leaveService;

    private Long employeeId(SecurityUser user) {
        Long id = userRepository.findById(user.getId()).map(u -> u.getEmployeeId()).orElse(null);
        if (id == null) {
            throw new BadRequestException("This account is not linked to an employee file.");
        }
        return id;
    }

    @GetMapping("/employee")
    public EmployeeDTO profile(@AuthenticationPrincipal SecurityUser user) {
        return hrService.getEmployeeById(employeeId(user));
    }

    @GetMapping("/salary-history")
    public List<SalaryHistoryDTO> salary(@AuthenticationPrincipal SecurityUser user) {
        return hrService.getSalaryHistoryForEmployee(employeeId(user));
    }

    @GetMapping("/trainings")
    public List<EmployeeTrainingDTO> trainings(@AuthenticationPrincipal SecurityUser user) {
        return hrService.getTrainingsForEmployee(employeeId(user));
    }

    @GetMapping("/surveys")
    public List<EngagementSurveyDTO> surveys(@AuthenticationPrincipal SecurityUser user) {
        return hrService.getSurveysForEmployee(employeeId(user));
    }

    @GetMapping("/reviews")
    public List<PerformanceReviewDTO> reviews(@AuthenticationPrincipal SecurityUser user) {
        return workforceService.getReviews(employeeId(user));
    }

    @GetMapping("/leave-requests")
    public List<LeaveRequestDTO> leave(@AuthenticationPrincipal SecurityUser user) {
        return leaveService.forEmployee(employeeId(user));
    }

    @PostMapping("/leave-requests")
    public LeaveRequestDTO requestLeave(@AuthenticationPrincipal SecurityUser user,
                                        @Valid @RequestBody LeaveRequestCreateDTO req) {
        return leaveService.request(employeeId(user), req);
    }
}
