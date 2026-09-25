package com.smarterp.shared.notification;

import com.smarterp.security.domain.RoleName;
import com.smarterp.security.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class NotificationService {

    private static final List<RoleName> HR_ROLES = List.of(RoleName.ROLE_ADMIN, RoleName.ROLE_HR_MANAGER);

    private final NotificationRepository repository;
    private final UserRepository userRepository;

    /** One notification for every active admin / HR manager. */
    @Transactional
    public void notifyHr(String title, String message, String link) {
        userRepository.findActiveByRoles(HR_ROLES)
                .forEach(u -> notifyUser(u.getId(), title, message, link));
    }

    /** Notification for the account linked to an employee (if any). */
    @Transactional
    public void notifyEmployee(Long employeeId, String title, String message, String link) {
        userRepository.findByEmployeeId(employeeId)
                .ifPresent(u -> notifyUser(u.getId(), title, message, link));
    }

    @Transactional
    public void notifyUser(UUID userId, String title, String message, String link) {
        Notification n = new Notification();
        n.setUserId(userId);
        n.setTitle(title);
        n.setMessage(message);
        n.setLink(link);
        repository.save(n);
    }

    @Transactional(readOnly = true)
    public List<NotificationDTO> latest(UUID userId) {
        return repository.findTop30ByUserIdOrderByCreatedAtDesc(userId).stream()
                .map(NotificationDTO::fromEntity).toList();
    }

    @Transactional(readOnly = true)
    public long unreadCount(UUID userId) {
        return repository.countByUserIdAndIsReadFalse(userId);
    }

    @Transactional
    public void markRead(UUID userId, Long id) {
        repository.findById(id)
                .filter(n -> n.getUserId().equals(userId))
                .ifPresent(n -> n.setIsRead(true));
    }

    @Transactional
    public void markAllRead(UUID userId) {
        repository.markAllRead(userId);
    }
}
