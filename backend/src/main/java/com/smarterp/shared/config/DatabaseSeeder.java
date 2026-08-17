package com.smarterp.shared.config;

import com.smarterp.security.domain.Role;
import com.smarterp.security.domain.RoleName;
import com.smarterp.security.domain.User;
import com.smarterp.security.repository.RoleRepository;
import com.smarterp.security.repository.UserRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Component
public class DatabaseSeeder implements CommandLineRunner {

    private final RoleRepository roleRepository;
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public DatabaseSeeder(RoleRepository roleRepository, UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.roleRepository = roleRepository;
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    @Transactional // Added to ensure the seeding happens cleanly in one transaction
    public void run(String... args) {
     
        // 1. Seed Roles if they don't exist (e.g., if Python ETL hasn't been run yet)
        for (RoleName roleName : RoleName.values()) {
            if (roleRepository.findByName(roleName).isEmpty()) {
                Role role = new Role();
                role.setName(roleName);
                role.setDescription("Standard " + roleName.name() + " access privileges");
                roleRepository.save(role);
            }
        }

        // 2. Seed Super Admin User
        if (!userRepository.existsByEmail("admin@smarterp.com")) {
            Role adminRole = roleRepository.findByName(RoleName.ROLE_ADMIN)
                    .orElseThrow(() -> new RuntimeException("Admin role not found during seeding"));
            
            User admin = new User();
            admin.setEmail("admin@smarterp.com");
            admin.setPasswordHash(passwordEncoder.encode("Admin@123456"));
            admin.setRole(adminRole);
            admin.setIsActive(true);
            
            // NOTE: We deliberately do NOT set employeeId here. 
            // This proves our architecture: The Super Admin is a User, but NOT an HR Employee!
            // admin.setEmployeeId(null); 

            userRepository.save(admin);
            System.out.println(">>> Seeded Super Admin account: admin@smarterp.com / Admin@123456");
        }
    }
}