package com.smarterp.admin;

import com.smarterp.security.domain.Role;
import com.smarterp.security.domain.RoleName;
import com.smarterp.security.domain.User;
import com.smarterp.security.repository.RoleRepository;
import com.smarterp.security.repository.UserRepository;
import com.smarterp.shared.audit.AuditLogDTO;
import com.smarterp.shared.audit.AuditLogRepository;
import com.smarterp.shared.audit.AuditService;
import com.smarterp.shared.exception.BadRequestException;
import com.smarterp.shared.exception.ResourceNotFoundException;
import com.smarterp.shared.security.CurrentUser;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AdminService {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final AuditLogRepository auditLogRepository;
    private final AuditService auditService;

    public Page<AdminUserDTO> users(int page, int size, String search, String role) {
        RoleName roleName = null;
        if (role != null && !role.isBlank()) {
            try {
                roleName = RoleName.valueOf(role);
            } catch (IllegalArgumentException e) {
                throw new BadRequestException("Unknown role: " + role);
            }
        }
        return userRepository.search(search, roleName, PageRequest.of(page, Math.min(size, 100), Sort.by("email")))
                .map(AdminUserDTO::fromEntity);
    }

    @Transactional
    public AdminUserDTO changeRole(UUID userId, String role) {
        User user = find(userId);
        preventSelfChange(user);
        RoleName name;
        try {
            name = RoleName.valueOf(role);
        } catch (IllegalArgumentException e) {
            throw new BadRequestException("Unknown role: " + role);
        }
        Role newRole = roleRepository.findByName(name)
                .orElseThrow(() -> new ResourceNotFoundException("Role " + name + " not found"));
        String old = user.getRole().getName().name();
        user.setRole(newRole);
        auditService.log("USER_ROLE_CHANGED", "user", user.getEmail(), old + " -> " + name);
        return AdminUserDTO.fromEntity(user);
    }

    @Transactional
    public AdminUserDTO setActive(UUID userId, boolean active) {
        User user = find(userId);
        preventSelfChange(user);
        user.setIsActive(active);
        auditService.log(active ? "USER_ENABLED" : "USER_DISABLED", "user", user.getEmail(), null);
        return AdminUserDTO.fromEntity(user);
    }

    public Page<AuditLogDTO> audit(int page, int size, String search) {
        return auditLogRepository.search(search, PageRequest.of(page, Math.min(size, 100)))
                .map(AuditLogDTO::fromEntity);
    }

    private User find(UUID id) {
        return userRepository.findById(id).orElseThrow(() -> new ResourceNotFoundException("No user with id " + id));
    }

    /** An admin must not lock themselves out. */
    private static void preventSelfChange(User user) {
        if (user.getEmail().equalsIgnoreCase(CurrentUser.email())) {
            throw new BadRequestException("You cannot change your own account here.");
        }
    }
}
