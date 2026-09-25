package com.smarterp.security.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record SetPasswordRequest(
        @NotBlank(message = "The token is required.") String token,
        @NotBlank(message = "The password is required.")
        @Size(min = 8, max = 100, message = "The password must be at least 8 characters long.")
        @Pattern(regexp = "^(?=.*[A-Za-z])(?=.*\\d).+$",
                 message = "The password must contain at least one letter and one digit.")
        String newPassword
) {}
