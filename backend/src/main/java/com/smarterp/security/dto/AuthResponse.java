package com.smarterp.security.dto;

import java.util.UUID;

public record AuthResponse(
    String accessToken,
    String tokenType,
    UUID userId,
    String email,
    String role
) {
    public AuthResponse(String accessToken, UUID userId, String email, String role) {
        this(accessToken, "Bearer", userId, email, role);
    }
}