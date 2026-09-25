package com.smarterp.security.service;

import com.smarterp.security.domain.Role;
import com.smarterp.security.domain.TokenType;
import com.smarterp.security.domain.User;
import com.smarterp.security.domain.UserToken;
import com.smarterp.security.dto.*;
import com.smarterp.security.repository.RoleRepository;
import com.smarterp.security.repository.UserRepository;
import com.smarterp.security.repository.UserTokenRepository;
import com.smarterp.shared.audit.AuditService;
import com.smarterp.shared.email.EmailService;
import com.smarterp.shared.exception.BadRequestException;
import com.smarterp.shared.exception.ResourceNotFoundException;
import com.smarterp.shared.security.JwtUtils;
import com.smarterp.shared.security.SecurityUser;
import com.smarterp.shared.transaction.AfterCommit;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
public class AuthService {

    private static final int ACTIVATION_MINUTES = 24 * 60;
    private static final int RESET_MINUTES = 60;

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final UserTokenRepository userTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtils jwtUtils;
    private final AuthenticationManager authenticationManager;
    private final EmailService emailService;
    private final AuditService auditService;

    @Value("${application.frontend-url:http://localhost:4200}")
    private String frontendUrl;

    public AuthService(UserRepository userRepository, RoleRepository roleRepository,
                       UserTokenRepository userTokenRepository, PasswordEncoder passwordEncoder,
                       JwtUtils jwtUtils, AuthenticationManager authenticationManager,
                       EmailService emailService, AuditService auditService) {
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.userTokenRepository = userTokenRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtUtils = jwtUtils;
        this.authenticationManager = authenticationManager;
        this.emailService = emailService;
        this.auditService = auditService;
    }

    /** Creates an account; the person chooses their password through the emailed activation link. */
    @Transactional
    public AuthResponse register(RegisterRequest request) {
        if (Boolean.TRUE.equals(userRepository.existsByEmail(request.email()))) {
            throw new BadRequestException("This email address is already used.");
        }
        Role role = roleRepository.findByName(request.role())
                .orElseThrow(() -> new ResourceNotFoundException("Role " + request.role() + " not found."));

        User user = new User();
        user.setEmail(request.email());
        user.setPasswordHash(passwordEncoder.encode(request.password()));
        user.setRole(role);
        user.setIsActive(true);
        User saved = userRepository.save(user);

        String token = UUID.randomUUID().toString();
        userTokenRepository.save(new UserToken(token, TokenType.ACTIVATION, saved, ACTIVATION_MINUTES));
        String activationUrl = frontendUrl + "/auth/set-password?token=" + token;
        AfterCommit.run(() -> emailService.sendAccountActivationEmail(request.email(), request.role().name(), activationUrl));

        auditService.log("USER_CREATED", "user", saved.getEmail(), request.role().name());
        return toResponse(saved);
    }

    public AuthResponse login(LoginRequest request) {
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.email(), request.password()));
        User user = userRepository.findByEmail(request.email())
                .orElseThrow(() -> new ResourceNotFoundException("No user with email " + request.email()));
        return toResponse(user);
    }

    /** Always succeeds from the caller's point of view, so the endpoint can't be used
     *  to find out which emails have an account. */
    @Transactional
    public void requestPasswordReset(ForgotPasswordRequest request) {
        userRepository.findByEmail(request.email().trim())
                .filter(u -> Boolean.TRUE.equals(u.getIsActive()))
                .ifPresent(user -> {
                    String token = UUID.randomUUID().toString();
                    userTokenRepository.save(new UserToken(token, TokenType.PASSWORD_RESET, user, RESET_MINUTES));
                    String resetUrl = frontendUrl + "/auth/set-password?token=" + token;
                    AfterCommit.run(() -> emailService.sendPasswordResetEmail(user.getEmail(), resetUrl));
                });
    }

    @Transactional
    public void setPasswordWithToken(SetPasswordRequest request) {
        UserToken token = userTokenRepository.findByToken(request.token())
                .orElseThrow(() -> new BadRequestException("Invalid link. Please ask for a new one."));

        // Only activation / reset links may set a password
        if (token.getTokenType() != TokenType.ACTIVATION && token.getTokenType() != TokenType.PASSWORD_RESET) {
            throw new BadRequestException("Invalid link. Please ask for a new one.");
        }
        if (!token.isUsable()) {
            throw new BadRequestException("This link has expired or was already used.");
        }

        User user = token.getUser();
        user.setPasswordHash(passwordEncoder.encode(request.newPassword()));
        userRepository.save(user);
        userTokenRepository.delete(token);
    }

    private AuthResponse toResponse(User user) {
        String jwt = jwtUtils.generateToken(new SecurityUser(user));
        return new AuthResponse(jwt, user.getId(), user.getEmployeeId(), user.getEmail(), user.getRole().getName().name());
    }
}
