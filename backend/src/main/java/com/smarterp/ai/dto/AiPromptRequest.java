package com.smarterp.ai.dto;

import jakarta.validation.constraints.NotBlank;
import java.util.Map;

public record AiPromptRequest(
    @NotBlank(message = "Prompt content cannot be empty")
    String prompt,
    Map<String, Object> context
) {}