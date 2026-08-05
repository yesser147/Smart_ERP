package com.smarterp.ai.domain;

import com.smarterp.security.domain.User;
import com.smarterp.shared.domain.BaseEntity;
import jakarta.persistence.*;
import java.util.UUID;

@Entity
@Table(name = "ai_query_logs")
public class AiQueryLog extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(columnDefinition = "TEXT", nullable = false)
    private String prompt;

    @Column(columnDefinition = "TEXT")
    private String response;

    @Column(name = "execution_time_ms")
    private Long executionTimeMs;

    public AiQueryLog() {}

    public AiQueryLog(User user, String prompt, String response, Long executionTimeMs) {
        this.user = user;
        this.prompt = prompt;
        this.response = response;
        this.executionTimeMs = executionTimeMs;
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }

    public String getPrompt() { return prompt; }
    public void setPrompt(String prompt) { this.prompt = prompt; }

    public String getResponse() { return response; }
    public void setResponse(String response) { this.response = response; }

    public Long getExecutionTimeMs() { return executionTimeMs; }
    public void setExecutionTimeMs(Long executionTimeMs) { this.executionTimeMs = executionTimeMs; }
}