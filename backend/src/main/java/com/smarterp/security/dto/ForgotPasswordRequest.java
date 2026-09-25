package com.smarterp.security.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

public record ForgotPasswordRequest(
        @NotBlank(message = "The email is required.") @Email(message = "Invalid email address.") String email
) {}
