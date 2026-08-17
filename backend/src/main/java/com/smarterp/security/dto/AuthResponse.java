package com.smarterp.security.dto;

import java.util.UUID;

public record AuthResponse(
    String accessToken,
    String tokenType,
    UUID userId,
    Long employeeId,
    String email,
    String role
) {
    public AuthResponse(String accessToken, UUID userId, Long employeeId, String email, String role) {
        this(accessToken, "Bearer", userId, employeeId, email, role);
    }
}