package com.smarterp.security.service;

import com.smarterp.security.domain.Role;
import com.smarterp.security.domain.RoleName;
import com.smarterp.security.domain.User;
import com.smarterp.security.dto.AuthResponse;
import com.smarterp.security.dto.LoginRequest;
import com.smarterp.security.dto.RegisterRequest;
import com.smarterp.security.dto.UserDTO;
import com.smarterp.security.repository.RoleRepository;
import com.smarterp.security.repository.UserRepository;
import com.smarterp.shared.exception.BadRequestException;
import com.smarterp.shared.exception.ResourceNotFoundException;
import com.smarterp.shared.security.JwtUtils;
import com.smarterp.shared.security.SecurityUser;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {

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
            AuthenticationManager authenticationManager
    ) {
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtUtils = jwtUtils;
        this.authenticationManager = authenticationManager;
    }

    @Transactional
    public AuthResponse register(RegisterRequest request) {
        if (userRepository.existsByEmail(request.email())) {
            throw new BadRequestException("Email address is already in use.");
        }

        Role role = roleRepository.findByName(request.role())
                .orElseThrow(() -> new ResourceNotFoundException("Error: Role " + request.role() + " was not found."));

        User user = new User();
        user.setEmail(request.email());
        user.setPasswordHash(passwordEncoder.encode(request.password()));
        user.setRole(role);
        user.setIsActive(true);

        User savedUser = userRepository.save(user);
        SecurityUser securityUser = new SecurityUser(savedUser);
        String jwtToken = jwtUtils.generateToken(securityUser);

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
                .orElseThrow(() -> new ResourceNotFoundException("User not found with email: " + request.email()));

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
                .orElseThrow(() -> new ResourceNotFoundException("User not found with email: " + email));

        return new UserDTO(
                user.getId(),
                user.getEmail(),
                user.getRole().getName().name(),
                user.getIsActive()
        );
    }
}