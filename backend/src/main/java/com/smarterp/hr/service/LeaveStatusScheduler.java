package com.smarterp.hr.service;

import com.smarterp.hr.repository.EmployeeRepository;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;

/**
 * Keeps employee_status in line with the approved leave requests:
 * "Active" -> "On Leave" on the first day, back to "Active" the day after the last one.
 * Runs every night, once at startup (catch-up), and right after a leave is approved.
 */
@Component
@RequiredArgsConstructor
public class LeaveStatusScheduler {

    private static final Logger log = LoggerFactory.getLogger(LeaveStatusScheduler.class);

    private final EmployeeRepository employeeRepository;

    @Scheduled(cron = "${application.leave-status-cron:0 5 0 * * *}")
    @EventListener(ApplicationReadyEvent.class)
    @Transactional
    public void syncStatuses() {
        LocalDate today = LocalDate.now();
        int started = employeeRepository.startApprovedLeaves(today);
        int ended = employeeRepository.endFinishedLeaves(today);
        if (started + ended > 0) {
            log.info("Leave statuses updated: {} now on leave, {} back to active", started, ended);
        }
    }
}
