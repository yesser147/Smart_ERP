package com.smarterp.security.repository;

import com.smarterp.security.domain.Role;
import com.smarterp.security.domain.RoleName;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
import java.util.UUID;

public interface RoleRepository extends JpaRepository<Role, Long> {
    Optional<Role> findByName(RoleName name);
}