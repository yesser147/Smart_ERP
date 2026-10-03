package com.smarterp.admin;

import com.smarterp.hr.domain.Employee;
import com.smarterp.hr.repository.EmployeeRepository;
import com.smarterp.security.domain.Role;
import com.smarterp.security.domain.RoleName;
import com.smarterp.security.domain.User;
import com.smarterp.security.repository.RoleRepository;
import com.smarterp.security.dto.AuthResponse;
import com.smarterp.security.dto.RegisterRequest;
import com.smarterp.security.repository.UserRepository;
import com.smarterp.security.service.AuthService;
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

import java.util.List;
import java.util.Set;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AdminService {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final AuditLogRepository auditLogRepository;
    private final AuditService auditService;
    private final EmployeeRepository employeeRepository;
    private final AuthService authService;

    private static final Set<String> CURRENT_STATUSES = Set.of("ACTIVE", "ON LEAVE");

    public List<EmployeeOptionDTO> employeesWithoutAccount(String search) {
        return employeeRepository.findWithoutAccount(search == null ? null : search.trim(), PageRequest.of(0, 20))
                .stream().map(EmployeeOptionDTO::fromEntity).toList();
    }

    /** A login for an employee who has none yet, with the role chosen by the admin. */
    @Transactional
    public AuthResponse createAccount(CreateAccountRequest req) {
        Employee employee = employeeRepository.findById(req.employeeId())
                .filter(e -> !Boolean.TRUE.equals(e.getIsDeleted()))
                .orElseThrow(() -> new ResourceNotFoundException("No employee with id " + req.employeeId()));
        String name = employee.getFirstName() + " " + employee.getLastName();
        String status = employee.getEmployeeStatus() == null ? "" : employee.getEmployeeStatus().toUpperCase();
        if (!CURRENT_STATUSES.contains(status)) {
            throw new BadRequestException(name + " is not a current employee (" + employee.getEmployeeStatus() + ").");
        }
        if (userRepository.findByEmployeeId(employee.getEmployeeId()).isPresent()) {
            throw new BadRequestException(name + " already has an account.");
        }
        AuthResponse account = authService.register(new RegisterRequest(req.email().trim(), req.password(), req.role()));
        find(account.userId()).setEmployeeId(employee.getEmployeeId());
        auditService.log("ACCOUNT_LINKED", "employee", employee.getEmployeeId(), req.email().trim() + " (" + req.role().name() + ")");
        return account;
    }

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
