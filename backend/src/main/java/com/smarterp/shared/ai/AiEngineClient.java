package com.smarterp.shared.ai;

import com.smarterp.shared.security.JwtUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.Map;

/** The backend's own calls to the FastAPI AI engine, signed with a short-lived service token. */
@Component
public class AiEngineClient {

    private final RestClient client;
    private final JwtUtils jwtUtils;

    public AiEngineClient(@Value("${ai.service.base-url:http://localhost:8000}") String baseUrl, JwtUtils jwtUtils) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5_000);
        factory.setReadTimeout(300_000);   // an LLM reading a CV can take a while
        this.client = RestClient.builder().baseUrl(baseUrl).requestFactory(factory).build();
        this.jwtUtils = jwtUtils;
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> processCv(Long applicantId) {
        return client.post()
                .uri("/api/ai/recruitment/process-cv/{id}", applicantId)
                .header("Authorization", "Bearer " + jwtUtils.generateServiceToken())
                .retrieve()
                .body(Map.class);
    }
}
