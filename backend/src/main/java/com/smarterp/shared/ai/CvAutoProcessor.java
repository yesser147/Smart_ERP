package com.smarterp.shared.ai;

import com.smarterp.shared.notification.NotificationService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/** Reads a new CV with the AI in the background, right after the application is saved. */
@Component
public class CvAutoProcessor {

    private static final Logger log = LoggerFactory.getLogger(CvAutoProcessor.class);

    private final AiEngineClient aiEngineClient;
    private final NotificationService notificationService;

    public CvAutoProcessor(AiEngineClient aiEngineClient, NotificationService notificationService) {
        this.aiEngineClient = aiEngineClient;
        this.notificationService = notificationService;
    }

    @Async
    public void process(Long applicantId, String applicantName, String jobTitle) {
        try {
            aiEngineClient.processCv(applicantId);
            notificationService.notifyHr("CV analysed",
                    "The CV of " + applicantName + " (" + jobTitle + ") was read by the AI and can be ranked.",
                    "/dashboard/applicant/" + applicantId);
        } catch (Exception e) {
            // not fatal: HR can still use the "Process CV" button later
            log.warn("Automatic CV processing failed for applicant {}: {}", applicantId, e.getMessage());
        }
    }
}
