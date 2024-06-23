package com.example.openipe.core.habits;

import java.util.List;

public class HabitStack {
    private String name;
    private List<Habit> habits;

    public HabitStack(String name, List<Habit> habits) {
        this.name = name;
        this.habits = habits;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public List<Habit> getHabits() {
        return habits;
    }

    public void setHabits(List<Habit> habits) {
        this.habits = habits;
    }
}
