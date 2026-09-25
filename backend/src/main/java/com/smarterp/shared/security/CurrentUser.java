package com.smarterp.shared.security;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

/** Who is calling: the logged-in user's email, or "SYSTEM" for background work. */
public final class CurrentUser {

    private CurrentUser() {}

    public static String email() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated() || "anonymousUser".equals(auth.getPrincipal())) {
            return "SYSTEM";
        }
        return auth.getName();
    }
}
