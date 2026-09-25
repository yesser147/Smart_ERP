package com.smarterp.security.repository;

import com.smarterp.security.domain.RoleName;
import com.smarterp.security.domain.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Collection;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface UserRepository extends JpaRepository<User, UUID> {
    Optional<User> findByEmail(String email);
    Boolean existsByEmail(String email);
    Optional<User> findByEmployeeId(Long employeeId);

    @Query("SELECT u FROM User u WHERE u.role.name IN :roles AND u.isActive = true")
    List<User> findActiveByRoles(@Param("roles") Collection<RoleName> roles);

    @Query("""
        SELECT u FROM User u
        WHERE (:search IS NULL OR :search = '' OR LOWER(u.email) LIKE LOWER(CONCAT('%', :search, '%')))
          AND (:role IS NULL OR u.role.name = :role)
    """)
    Page<User> search(@Param("search") String search, @Param("role") RoleName role, Pageable pageable);
}
