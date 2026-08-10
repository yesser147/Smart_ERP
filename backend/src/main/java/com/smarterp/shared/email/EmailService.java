package com.smarterp.shared.email;

import jakarta.mail.internet.MimeMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;
import org.thymeleaf.TemplateEngine;
import org.thymeleaf.context.Context;

@Service
public class EmailService {

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

            MimeMessage mimeMessage = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, true, "UTF-8");

            helper.setFrom("nexuserp.system@gmail.com");
            helper.setTo(toEmail);
            helper.setSubject("Bienvenue sur Nexus ERP - Activez votre compte");
            helper.setText(htmlContent, true);

            mailSender.send(mimeMessage);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}