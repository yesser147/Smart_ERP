package com.smarterp.shared.transaction;

import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

/**
 * Runs an action (typically sending an email) only once the current database
 * transaction has committed, so a rollback never leaves a sent email behind.
 * Outside a transaction the action runs immediately.
 */
public final class AfterCommit {

    private AfterCommit() {}

    public static void run(Runnable action) {
        if (TransactionSynchronizationManager.isSynchronizationActive()) {
            TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                @Override
                public void afterCommit() {
                    action.run();
                }
            });
        } else {
            action.run();
        }
    }
}
