package com.example.openipe.habits;

import android.provider.BaseColumns;

public final class HabitContract {

    private HabitContract() {}

    public static class HabitEntry implements BaseColumns {
        public static final String TABLE_NAME = "habits";
        public static final String COLUMN_DESCRIPTION = "description";
        public static final String COLUMN_RECURRENCE = "recurrence";
        public static final String COLUMN_STACK_NAME = "stack_name";
        public static final String COLUMN_DUE_TIMESTAMP = "due_timestamp";
        public static final String COLUMN_IS_COMPLETED = "is_completed";
    }

    public static class HistoryEntry implements BaseColumns {
        public static final String TABLE_NAME = "history";
        public static final String COLUMN_HABIT_ID = "habit_id";
        public static final String COLUMN_COMPLETION_TIMESTAMP = "completion_timestamp";
    }
}
