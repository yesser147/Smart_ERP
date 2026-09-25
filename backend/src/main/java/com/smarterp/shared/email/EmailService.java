package com.smarterp.shared.email;

import jakarta.mail.internet.MimeMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;
import org.thymeleaf.TemplateEngine;
import org.thymeleaf.context.Context;

import java.util.Map;

/** HTML emails from the Thymeleaf templates. A failure is logged, never thrown:
 *  the business action (hire, status change...) must not fail because of the mail server. */
@Service
public class EmailService {

    private static final Logger log = LoggerFactory.getLogger(EmailService.class);

    private final JavaMailSender mailSender;
    private final TemplateEngine templateEngine;
    private final String fromAddress;

    public EmailService(JavaMailSender mailSender, TemplateEngine templateEngine,
                        @Value("${spring.mail.username}") String fromAddress) {
        this.mailSender = mailSender;
        this.templateEngine = templateEngine;
        this.fromAddress = fromAddress;
    }

    public void sendAccountActivationEmail(String to, String role, String activationUrl) {
        send(to, "Welcome to Nexus ERP - activate your account", "welcome-email",
                Map.of("email", to, "role", role, "activationUrl", activationUrl));
    }

    public void sendPasswordResetEmail(String to, String resetUrl) {
        send(to, "Nexus ERP - reset your password", "password-reset-email", Map.of("resetUrl", resetUrl));
    }

    public void sendInterviewInvitationEmail(String to, String applicantName, String jobTitle) {
        send(to, "Interview invitation - " + jobTitle, "interview-invitation-email",
                Map.of("applicantName", applicantName, "jobTitle", jobTitle));
    }

    public void sendOfferEmail(String to, String applicantName, String jobTitle) {
        send(to, "Job offer - " + jobTitle, "offer-email",
                Map.of("applicantName", applicantName, "jobTitle", jobTitle));
    }

    public void sendRejectionEmail(String to, String applicantName, String jobTitle) {
        send(to, "About your application - " + jobTitle, "rejection-email",
                Map.of("applicantName", applicantName, "jobTitle", jobTitle));
    }

    private void send(String to, String subject, String template, Map<String, Object> variables) {
        try {
            Context context = new Context();
            variables.forEach(context::setVariable);
            String html = templateEngine.process(template, context);

            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
            helper.setFrom(fromAddress);
            helper.setTo(to);
            helper.setSubject(subject);
            helper.setText(html, true);
            mailSender.send(message);
        } catch (Exception e) {
            log.error("Could not send the '{}' email to {}", template, to, e);
        }
    }
}
