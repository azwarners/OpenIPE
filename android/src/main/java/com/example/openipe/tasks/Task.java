package com.example.openipe.tasks;

public class Task {
    private long id;
    private String description;
    private String project;
    private String context;
    private long dueTimestamp;
    private boolean isCompleted;

    public Task(long id, String description, String project, String stackName, long dueTimestamp, boolean isCompleted) {
        this.id = id;
        this.description = description;
        this.project = project;
        this.context = stackName;
        this.dueTimestamp = dueTimestamp;
        this.isCompleted = isCompleted;
    }

    // Additional constructor without id for new habits
    public Task(String description, String recurrence, String stackName, long dueTimestamp, boolean isCompleted) {
        this.description = description;
        this.project = recurrence;
        this.context = stackName;
        this.dueTimestamp = dueTimestamp;
        this.isCompleted = isCompleted;
    }

    // Getters
    public long getId() {
        return id;
    }

    public String getDescription() {
        return description;
    }

    public String getProject() {
        return project;
    }

    public String getContext() {
        return context;
    }

    public long getDueTimestamp() {
        return dueTimestamp;
    }

    public boolean getIsCompleted() { return isCompleted; }

    // Setters
    public void setId(long id) {
        this.id = id;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public void setProject(String project) {
        this.project = project;
    }

    public void setContext(String context) {
        this.context = context;
    }

    public void setDueTimestamp(long dueTimestamp) {
        this.dueTimestamp = dueTimestamp;
    }

    public void setIsCompleted(boolean isCompleted) {
        this.isCompleted = isCompleted;
    }
}
