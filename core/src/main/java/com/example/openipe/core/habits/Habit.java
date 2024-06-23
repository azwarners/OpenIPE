package com.example.openipe.core.habits;

import java.util.ArrayList;
import java.util.List;

public class Habit {
    private long id;
    private String description;
    private String recurrence;
    private String stackName;
    private long dueTimestamp;
    private boolean isCompleted;
    private List<Long> completionHistory;

    public Habit(long id, String description, String recurrence, String stackName, long dueTimestamp, boolean isCompleted) {
        this.id = id;
        this.description = description;
        this.recurrence = recurrence;
        this.stackName = stackName;
        this.dueTimestamp = dueTimestamp;
        this.isCompleted = isCompleted;
        this.completionHistory = new ArrayList<>();
    }

    public void addCompletion(long timestamp) {
        completionHistory.add(timestamp);
    }

    // Getters and Setters
    public long getId() {
        return id;
    }

    public void setId(long id) {
        this.id = id;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getRecurrence() {
        return recurrence;
    }

    public void setRecurrence(String recurrence) {
        this.recurrence = recurrence;
    }

    public String getStackName() {
        return stackName;
    }

    public void setStackName(String stackName) {
        this.stackName = stackName;
    }

    public long getDueTimestamp() {
        return dueTimestamp;
    }

    public void setDueTimestamp(long dueTimestamp) {
        this.dueTimestamp = dueTimestamp;
    }

    public boolean getIsCompleted() {
        return isCompleted;
    }

    public void setIsCompleted(boolean isCompleted) {
        this.isCompleted = isCompleted;
    }

    public List<Long> getCompletionHistory() {
        return completionHistory;
    }

    public void setCompletionHistory(List<Long> completionHistory) {
        this.completionHistory = completionHistory;
    }
}
