package com.smarterp.security.domain;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "user_tokens")
public class UserToken {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, unique = true)
    private String token;

    @Enumerated(EnumType.STRING)
    @Column(name = "token_type", nullable = false, length = 50)
    private TokenType tokenType;

    // Notice we use @ManyToOne instead of @OneToOne! 
    // A user might have a Refresh Token AND a Password Reset Token at the same time.
    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(nullable = false, name = "user_id")
    private User user;

    @Column(name = "expires_at", nullable = false)
    private LocalDateTime expiryDate;

    @Column(name = "is_used")
    private Boolean used = false;

    @Column(name = "is_revoked")
    private Boolean revoked = false;

    public UserToken() {}

    public UserToken(String token, TokenType tokenType, User user, int expirationInMinutes) {
        this.token = token;
        this.tokenType = tokenType;
        this.user = user;
        this.expiryDate = LocalDateTime.now().plusMinutes(expirationInMinutes);
    }

    public boolean isExpired() {
        return LocalDateTime.now().isAfter(this.expiryDate);
    }

    /** A token can set a password once, if it wasn't revoked and hasn't expired. */
    public boolean isUsable() {
        return !Boolean.TRUE.equals(used) && !Boolean.TRUE.equals(revoked) && !isExpired();
    }

    // Getters and Setters
    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public String getToken() { return token; }
    public void setToken(String token) { this.token = token; }

    public TokenType getTokenType() { return tokenType; }
    public void setTokenType(TokenType tokenType) { this.tokenType = tokenType; }

    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }

    public LocalDateTime getExpiryDate() { return expiryDate; }

    public Boolean getUsed() { return used; }
    public void setUsed(Boolean used) { this.used = used; }

    public Boolean getRevoked() { return revoked; }
    public void setRevoked(Boolean revoked) { this.revoked = revoked; }
    public void setExpiryDate(LocalDateTime expiryDate) { this.expiryDate = expiryDate; }
}