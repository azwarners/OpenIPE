package com.example.openipe.core.habits;

public final class HabitSchema {

    private HabitSchema() {}

    public static class HabitEntry {
        public static final String TABLE_NAME = "habits";
        public static final String _ID = "id";
        public static final String COLUMN_DESCRIPTION = "description";
        public static final String COLUMN_RECURRENCE = "recurrence";
        public static final String COLUMN_STACK_NAME = "stackName";
        public static final String COLUMN_DUE_TIMESTAMP = "dueTimestamp";
        public static final String COLUMN_IS_COMPLETED = "isCompleted";
    }

    public static class HistoryEntry {
        public static final String TABLE_NAME = "habit_history";
        public static final String _ID = "id";
        public static final String COLUMN_HABIT_ID = "habit_id";
        public static final String COLUMN_COMPLETION_TIMESTAMP = "completion_timestamp";
    }
}
