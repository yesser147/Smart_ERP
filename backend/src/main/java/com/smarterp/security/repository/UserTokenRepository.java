package com.smarterp.security.repository;

import com.smarterp.security.domain.UserToken;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
import java.util.UUID;

public interface UserTokenRepository extends JpaRepository<UserToken, UUID> {
    Optional<UserToken> findByToken(String token);
    void deleteByUserId(UUID userId);
}