package com.smarterp.security.service;

import com.smarterp.security.domain.PasswordResetToken;
import com.smarterp.security.domain.Role;
import com.smarterp.security.domain.User;
import com.smarterp.security.dto.AuthResponse;
import com.smarterp.security.dto.LoginRequest;
import com.smarterp.security.dto.RegisterRequest;
import com.smarterp.security.dto.SetPasswordRequest;
import com.smarterp.security.dto.UserDTO;
import com.smarterp.security.repository.PasswordResetTokenRepository;
import com.smarterp.security.repository.RoleRepository;
import com.smarterp.security.repository.UserRepository;
import com.smarterp.shared.email.EmailService;
import com.smarterp.shared.exception.BadRequestException;
import com.smarterp.shared.exception.ResourceNotFoundException;
import com.smarterp.shared.security.JwtUtils;
import com.smarterp.shared.security.SecurityUser;

import java.util.UUID;

import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {

    private final PasswordResetTokenRepository passwordResetTokenRepository;
    private final EmailService emailService;
    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtils jwtUtils;
    private final AuthenticationManager authenticationManager;

    public AuthService(
            UserRepository userRepository,
            RoleRepository roleRepository,
            PasswordEncoder passwordEncoder,
            JwtUtils jwtUtils,
            AuthenticationManager authenticationManager, 
            EmailService emailService, 
            PasswordResetTokenRepository passwordResetTokenRepository
    ) {
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtUtils = jwtUtils;
        this.authenticationManager = authenticationManager;
        this.emailService = emailService;
        this.passwordResetTokenRepository = passwordResetTokenRepository;
    }

    @Transactional //enable the rollback
    public AuthResponse register(RegisterRequest request) {
        if (userRepository.existsByEmail(request.email())) {
            throw new BadRequestException("Cette adresse e-mail est déjà utilisée.");
        }

        Role role = roleRepository.findByName(request.role())
                .orElseThrow(() -> new ResourceNotFoundException("Erreur : Le rôle " + request.role() + " est introuvable."));

        User user = new User();
        user.setEmail(request.email());
        user.setPasswordHash(passwordEncoder.encode(request.password()));
        user.setRole(role);
        user.setIsActive(true);

        User savedUser = userRepository.save(user);

        String token = UUID.randomUUID().toString();
        PasswordResetToken resetToken = new PasswordResetToken(token, savedUser, 24);
        passwordResetTokenRepository.save(resetToken);

        SecurityUser securityUser = new SecurityUser(savedUser);
        String jwtToken = jwtUtils.generateToken(securityUser);
        String activationUrl = "http://localhost:4200/auth/set-password?token=" + token;
        
        emailService.sendAccountActivationEmail(request.email(), request.role().name(), activationUrl);

        return new AuthResponse(
                jwtToken,
                savedUser.getId(),
                savedUser.getEmail(),
                savedUser.getRole().getName().name()
        );
    }

    public AuthResponse login(LoginRequest request) {
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.email(), request.password())
        );

        User user = userRepository.findByEmail(request.email())
                .orElseThrow(() -> new ResourceNotFoundException("Aucun utilisateur trouvé avec l'e-mail : " + request.email()));

        SecurityUser securityUser = new SecurityUser(user);
        String jwtToken = jwtUtils.generateToken(securityUser);

        return new AuthResponse(
                jwtToken,
                user.getId(),
                user.getEmail(),
                user.getRole().getName().name()
        );
    }

    @Transactional(readOnly = true)
    public UserDTO getCurrentUser(String email) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("Aucun utilisateur trouvé avec l'e-mail : " + email));

        return new UserDTO(
                user.getId(),
                user.getEmail(),
                user.getRole().getName().name(),
                user.getIsActive()
        );
}

       @Transactional 
        public void setPasswordWithToken(SetPasswordRequest request) {
    if (request == null || request.getToken() == null || request.getNewPassword() == null) {
        throw new BadRequestException("Le jeton et le mot de passe sont obligatoires.");
    }

    PasswordResetToken resetToken = passwordResetTokenRepository.findByToken(request.getToken())
            .orElseThrow(() -> new BadRequestException("Jeton invalide ou introuvable. Veuillez refaire une demande."));

    if (resetToken.isExpired()) {
        passwordResetTokenRepository.delete(resetToken);
        throw new BadRequestException("Ce lien d'activation a expiré.");
    }

    User user = resetToken.getUser();
    user.setPasswordHash(passwordEncoder.encode(request.getNewPassword()));
    
    // Save updated user and delete single-use token
    userRepository.save(user);
    passwordResetTokenRepository.delete(resetToken);
}
}