package com.smarterp.security.dto;

import java.util.UUID;

public record UserDTO(
    UUID id,
    Long employeeId,
    String email,
    String role,
    Boolean isActive
) {}