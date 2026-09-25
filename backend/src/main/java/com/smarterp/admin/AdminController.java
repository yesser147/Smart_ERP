package com.smarterp.admin;

import com.smarterp.shared.audit.AuditLogDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

/** User & role management and the audit log (ROLE_ADMIN only, see SecurityConfig). */
@RestController
@RequestMapping("/admin")
@RequiredArgsConstructor
public class AdminController {

    private final AdminService service;

    @GetMapping("/users")
    public Page<AdminUserDTO> users(@RequestParam(defaultValue = "0") int page,
                                    @RequestParam(defaultValue = "25") int size,
                                    @RequestParam(required = false) String search,
                                    @RequestParam(required = false) String role) {
        return service.users(page, size, search, role);
    }

    @PatchMapping("/users/{id}/role")
    public AdminUserDTO changeRole(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        return service.changeRole(id, body.get("role"));
    }

    @PatchMapping("/users/{id}/active")
    public AdminUserDTO setActive(@PathVariable UUID id, @RequestBody Map<String, Boolean> body) {
        return service.setActive(id, Boolean.TRUE.equals(body.get("active")));
    }

    @GetMapping("/audit")
    public Page<AuditLogDTO> audit(@RequestParam(defaultValue = "0") int page,
                                   @RequestParam(defaultValue = "50") int size,
                                   @RequestParam(required = false) String search) {
        return service.audit(page, size, search);
    }
}
