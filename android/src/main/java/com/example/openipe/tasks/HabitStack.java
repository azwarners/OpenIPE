package com.example.openipe.tasks;

import java.util.List;

public class HabitStack {
    private String name;
    private List<Task> habits;

    public HabitStack(String name, List<Task> habits) {
        this.setName(name);
        this.setHabits(habits);
    }

    // Getters and setters

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public List<Task> getHabits() {
        return habits;
    }

    public void setHabits(List<Task> habits) {
        this.habits = habits;
    }

}
