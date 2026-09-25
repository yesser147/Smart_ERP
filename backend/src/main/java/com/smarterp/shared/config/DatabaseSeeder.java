package com.smarterp.shared.config;

import com.smarterp.security.domain.Role;
import com.smarterp.security.domain.RoleName;
import com.smarterp.security.domain.User;
import com.smarterp.security.repository.RoleRepository;
import com.smarterp.security.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/** Creates the roles and the first administrator (credentials from ADMIN_EMAIL / ADMIN_PASSWORD). */
@Component
public class DatabaseSeeder implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(DatabaseSeeder.class);

    private final RoleRepository roleRepository;
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Value("${application.admin.email:yasser.saidani@fsb.ucar.tn}")
    private String adminEmail;

    @Value("${application.admin.password:Admin@123456}")
    private String adminPassword;

    public DatabaseSeeder(RoleRepository roleRepository, UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.roleRepository = roleRepository;
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    @Transactional
    public void run(String... args) {
        for (RoleName roleName : RoleName.values()) {
            if (roleRepository.findByName(roleName).isEmpty()) {
                Role role = new Role();
                role.setName(roleName);
                role.setDescription(roleName.name());
                roleRepository.save(role);
            }
        }

        if (!Boolean.TRUE.equals(userRepository.existsByEmail(adminEmail))) {
            User admin = new User();
            admin.setEmail(adminEmail);
            admin.setPasswordHash(passwordEncoder.encode(adminPassword));
            admin.setRole(roleRepository.findByName(RoleName.ROLE_ADMIN).orElseThrow());
            admin.setIsActive(true);
            userRepository.save(admin);   // not an employee: no employeeId
            log.info("Created the administrator account {}", adminEmail);
        }
    }
}
