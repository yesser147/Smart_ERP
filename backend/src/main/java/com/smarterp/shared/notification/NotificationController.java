package com.smarterp.shared.notification;

import com.smarterp.shared.security.SecurityUser;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/notifications")
@RequiredArgsConstructor
public class NotificationController {

    private final NotificationService service;

    @GetMapping
    public ResponseEntity<Map<String, Object>> mine(@AuthenticationPrincipal SecurityUser user) {
        List<NotificationDTO> items = service.latest(user.getId());
        return ResponseEntity.ok(Map.of("unread", service.unreadCount(user.getId()), "items", items));
    }

    @PostMapping("/{id}/read")
    public ResponseEntity<Void> read(@AuthenticationPrincipal SecurityUser user, @PathVariable Long id) {
        service.markRead(user.getId(), id);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/read-all")
    public ResponseEntity<Void> readAll(@AuthenticationPrincipal SecurityUser user) {
        service.markAllRead(user.getId());
        return ResponseEntity.noContent().build();
    }
}
