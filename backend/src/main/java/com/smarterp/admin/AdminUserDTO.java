package com.smarterp.admin;

import com.smarterp.security.domain.User;

import java.time.LocalDateTime;
import java.util.UUID;

public record AdminUserDTO(UUID id, String email, String role, boolean active, Long employeeId,
                           LocalDateTime createdAt) {

    public static AdminUserDTO fromEntity(User u) {
        return new AdminUserDTO(u.getId(), u.getEmail(), u.getRole().getName().name(),
                Boolean.TRUE.equals(u.getIsActive()), u.getEmployeeId(), u.getCreatedAt());
    }
}
