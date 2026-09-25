package com.smarterp.security.dto;

import com.smarterp.security.domain.RoleName;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/** Same password rule as SetPasswordRequest. */
public record RegisterRequest(
    @NotBlank(message = "The e-mail is required.")
    @Email(message = "Invalid e-mail address.")
    String email,

    @NotBlank(message = "The password is required.")
    @Size(min = 8, max = 100, message = "The password must be at least 8 characters long.")
    @Pattern(regexp = "^(?=.*[A-Za-z])(?=.*\\d).+$",
             message = "The password must contain at least one letter and one digit.")
    String password,

    @NotNull(message = "The role is required.")
    RoleName role
) {}
