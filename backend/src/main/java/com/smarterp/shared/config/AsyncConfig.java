package com.smarterp.shared.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;

/** Enables @Async (background CV processing). */
@Configuration
@EnableAsync
public class AsyncConfig {
}
