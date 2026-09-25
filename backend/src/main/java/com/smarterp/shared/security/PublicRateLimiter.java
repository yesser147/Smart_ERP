package com.smarterp.shared.security;

import com.smarterp.shared.exception.TooManyRequestsException;
import org.springframework.stereotype.Component;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/** Limits anonymous job applications per IP address (sliding window, in memory). */
@Component
public class PublicRateLimiter {

    private static final int MAX_REQUESTS = 5;
    private static final long WINDOW_MS = 10 * 60 * 1000;

    private final Map<String, Deque<Long>> hits = new ConcurrentHashMap<>();

    public void check(String clientIp) {
        long now = System.currentTimeMillis();
        Deque<Long> times = hits.computeIfAbsent(clientIp, k -> new ArrayDeque<>());
        synchronized (times) {
            while (!times.isEmpty() && now - times.peekFirst() > WINDOW_MS) {
                times.pollFirst();
            }
            if (times.size() >= MAX_REQUESTS) {
                throw new TooManyRequestsException("Too many applications from your network. Please try again in a few minutes.");
            }
            times.addLast(now);
        }
    }
}
