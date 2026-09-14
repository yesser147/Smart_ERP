package com.smarterp.shared.email;

import jakarta.mail.internet.MimeMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;
import org.thymeleaf.TemplateEngine;
import org.thymeleaf.context.Context;

@Service
public class EmailService {

    private static final Logger log = LoggerFactory.getLogger(EmailService.class);

    private final JavaMailSender mailSender;
    private final TemplateEngine templateEngine;

    public EmailService(JavaMailSender mailSender, TemplateEngine templateEngine) {
        this.mailSender = mailSender;
        this.templateEngine = templateEngine;
    }

    public void sendAccountActivationEmail(String toEmail, String role, String activationUrl) {
        try {
            Context context = new Context();
            context.setVariable("email", toEmail);
            context.setVariable("role", role);
            context.setVariable("activationUrl", activationUrl);

            String htmlContent = templateEngine.process("welcome-email", context);
            sendHtml(toEmail, "Bienvenue sur Nexus ERP - Activez votre compte", htmlContent);
        } catch (Exception e) {
            log.error("Échec de l'envoi de l'email d'activation à {}", toEmail, e);
        }
    }

    public void sendInterviewInvitationEmail(String toEmail, String applicantName, String jobTitle) {
        try {
            Context context = new Context();
            context.setVariable("applicantName", applicantName);
            context.setVariable("jobTitle", jobTitle);

            String htmlContent = templateEngine.process("interview-invitation-email", context);
            sendHtml(toEmail, "Invitation à un entretien - " + jobTitle, htmlContent);
        } catch (Exception e) {
            log.error("Échec de l'envoi de l'email d'entretien à {}", toEmail, e);
        }
    }

    public void sendOfferEmail(String toEmail, String applicantName, String jobTitle) {
        try {
            Context context = new Context();
            context.setVariable("applicantName", applicantName);
            context.setVariable("jobTitle", jobTitle);

            String htmlContent = templateEngine.process("offer-email", context);
            sendHtml(toEmail, "Offre d'emploi - " + jobTitle, htmlContent);
        } catch (Exception e) {
            log.error("Échec de l'envoi de l'email d'offre à {}", toEmail, e);
        }
    }

    public void sendRejectionEmail(String toEmail, String applicantName, String jobTitle) {
        try {
            Context context = new Context();
            context.setVariable("applicantName", applicantName);
            context.setVariable("jobTitle", jobTitle);

            String htmlContent = templateEngine.process("rejection-email", context);
            sendHtml(toEmail, "Concernant votre candidature - " + jobTitle, htmlContent);
        } catch (Exception e) {
            log.error("Échec de l'envoi de l'email de rejet à {}", toEmail, e);
        }
    }

    private void sendHtml(String toEmail, String subject, String htmlContent) throws Exception {
        MimeMessage mimeMessage = mailSender.createMimeMessage();
        MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, true, "UTF-8");

        helper.setFrom("nexuserp.system@gmail.com");
        helper.setTo(toEmail);
        helper.setSubject(subject);
        helper.setText(htmlContent, true);

        mailSender.send(mimeMessage);
    }
}