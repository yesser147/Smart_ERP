package com.smarterp.security.web;

import com.smarterp.security.dto.*;
import com.smarterp.security.service.AuthService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/register")
    public ResponseEntity<AuthResponse> register(@Valid @RequestBody RegisterRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(authService.register(request));
    }

    @PostMapping("/login")
    public AuthResponse login(@Valid @RequestBody LoginRequest request) {
        return authService.login(request);
    }

    @PostMapping("/forgot-password")
    public Map<String, String> forgotPassword(@Valid @RequestBody ForgotPasswordRequest request) {
        authService.requestPasswordReset(request);
        return Map.of("message", "If an account exists for this email, a reset link has been sent.");
    }

    @PostMapping("/set-password")
    public Map<String, String> setPassword(@Valid @RequestBody SetPasswordRequest request) {
        authService.setPasswordWithToken(request);
        return Map.of("message", "Password saved. You can now sign in.");
    }
}
