package com.smarterp.shared.audit;

import com.smarterp.shared.security.CurrentUser;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

/** Records who did what. Joins the caller's transaction, so a rolled-back action leaves no trace. */
@Service
@RequiredArgsConstructor
public class AuditService {

    private final AuditLogRepository repository;

    @Transactional(propagation = Propagation.REQUIRED)
    public void log(String action, String entityType, Object entityId, String details) {
        AuditLog entry = new AuditLog();
        entry.setActor(CurrentUser.email());
        entry.setAction(action);
        entry.setEntityType(entityType);
        entry.setEntityId(entityId == null ? null : String.valueOf(entityId));
        entry.setDetails(details);
        repository.save(entry);
    }
}
