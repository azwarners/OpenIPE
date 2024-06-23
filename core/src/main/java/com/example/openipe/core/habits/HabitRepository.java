package com.example.openipe.core.habits;

import java.util.List;

public interface HabitRepository {
    void addHabit(Habit habit);
    void updateHabit(Habit habit);
    List<Habit> getAllHabits();
    List<HabitStack> getAllHabitStacks();
    void deleteAllHabits();
}
