package com.smarterp.shared.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/** Enables @Async (background CV processing) and @Scheduled (nightly leave status update). */
@Configuration
@EnableAsync
@EnableScheduling
public class AsyncConfig {
}
