package com.smarterp.security.dto;

import java.util.UUID;

public record UserDTO(
    UUID id,
    String email,
    String role,
    Boolean isActive
) {}