package com.smarterp.shared.security;

import com.smarterp.shared.exception.TooManyRequestsException;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.assertj.core.api.Assertions.assertThatCode;

class PublicRateLimiterTest {

    @Test
    void sixthApplicationFromTheSameIpIsRefused() {
        PublicRateLimiter limiter = new PublicRateLimiter();
        for (int i = 0; i < 5; i++) {
            limiter.check("10.0.0.1");
        }
        assertThatThrownBy(() -> limiter.check("10.0.0.1")).isInstanceOf(TooManyRequestsException.class);
        assertThatCode(() -> limiter.check("10.0.0.2")).doesNotThrowAnyException();
    }
}
