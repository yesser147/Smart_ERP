package com.smarterp.shared.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

@Component
public class JwtUtils {

    private static final long SERVICE_TOKEN_MS = 5 * 60 * 1000;

    @Value("${application.security.jwt.secret-key}")
    private String secretKey;

    @Value("${application.security.jwt.expiration-ms:86400000}")
    private long jwtExpiration;

    public String extractUsername(String token) {
        return claims(token).getSubject();
    }

    /** Login token. The role travels in the token so the AI engine can check it without the database. */
    public String generateToken(UserDetails user) {
        Map<String, Object> claims = new HashMap<>();
        user.getAuthorities().stream().findFirst().ifPresent(a -> claims.put("role", a.getAuthority()));
        return build(claims, user.getUsername(), jwtExpiration);
    }

    /** Short-lived token for the backend's own calls to the AI engine (background CV processing). */
    public String generateServiceToken() {
        return build(Map.of("role", "ROLE_ADMIN", "service", true), "system@nexus-erp.internal", SERVICE_TOKEN_MS);
    }

    public boolean validateToken(String token) {
        try {
            claims(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }

    private String build(Map<String, Object> claims, String subject, long validityMs) {
        long now = System.currentTimeMillis();
        return Jwts.builder()
                .claims(claims)
                .subject(subject)
                .issuedAt(new Date(now))
                .expiration(new Date(now + validityMs))
                .signWith(signingKey())
                .compact();
    }

    private Claims claims(String token) {
        return Jwts.parser().verifyWith(signingKey()).build().parseSignedClaims(token).getPayload();
    }

    private SecretKey signingKey() {
        return Keys.hmacShaKeyFor(Decoders.BASE64.decode(secretKey));
    }
}
