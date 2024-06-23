package com.example.openipe.tasks;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;

import java.util.ArrayList;
import java.util.List;

public class HabitDbHandler {

    private HabitDbHelper dbHelper;

    public HabitDbHandler(Context context) {
        dbHelper = new HabitDbHelper(context);
    }

    public void addHabit(Task habit) {
        SQLiteDatabase db = dbHelper.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put(HabitContract.HabitEntry.COLUMN_DESCRIPTION, habit.getDescription());
        values.put(HabitContract.HabitEntry.COLUMN_RECURRENCE, habit.getProject());
        values.put(HabitContract.HabitEntry.COLUMN_STACK_NAME, habit.getContext());
        values.put(HabitContract.HabitEntry.COLUMN_DUE_TIMESTAMP, habit.getDueTimestamp());
        values.put(HabitContract.HabitEntry.COLUMN_IS_COMPLETED, habit.getIsCompleted() ? 1 : 0);
        db.insert(HabitContract.HabitEntry.TABLE_NAME, null, values);
        db.close();
    }

    public void updateHabit(Task habit) {
        SQLiteDatabase db = dbHelper.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put(HabitContract.HabitEntry.COLUMN_DESCRIPTION, habit.getDescription());
        values.put(HabitContract.HabitEntry.COLUMN_RECURRENCE, habit.getProject());
        values.put(HabitContract.HabitEntry.COLUMN_STACK_NAME, habit.getContext());
        values.put(HabitContract.HabitEntry.COLUMN_DUE_TIMESTAMP, habit.getDueTimestamp());
        values.put(HabitContract.HabitEntry.COLUMN_IS_COMPLETED, habit.getIsCompleted() ? 1 : 0);

        String selection = HabitContract.HabitEntry._ID + " = ?";
        String[] selectionArgs = { String.valueOf(habit.getId()) };

        db.update(HabitContract.HabitEntry.TABLE_NAME, values, selection, selectionArgs);
        db.close();
    }

    public List<Task> getAllHabits() {
        List<Task> habits = new ArrayList<>();
        SQLiteDatabase db = dbHelper.getReadableDatabase();
        Cursor cursor = db.query(HabitContract.HabitEntry.TABLE_NAME, null, null, null, null, null, null);
        if (cursor.moveToFirst()) {
            do {
                long id = cursor.getLong(cursor.getColumnIndex(HabitContract.HabitEntry._ID));
                String description = cursor.getString(cursor.getColumnIndex(HabitContract.HabitEntry.COLUMN_DESCRIPTION));
                String recurrence = cursor.getString(cursor.getColumnIndex(HabitContract.HabitEntry.COLUMN_RECURRENCE));
                String stackName = cursor.getString(cursor.getColumnIndex(HabitContract.HabitEntry.COLUMN_STACK_NAME));
                long dueTimestamp = cursor.getLong(cursor.getColumnIndex(HabitContract.HabitEntry.COLUMN_DUE_TIMESTAMP));
                boolean isCompleted = cursor.getInt(cursor.getColumnIndex(HabitContract.HabitEntry.COLUMN_IS_COMPLETED)) == 1;
                Task habit = new Task(id, description, recurrence, stackName, dueTimestamp, isCompleted);
                habits.add(habit);
            } while (cursor.moveToNext());
        }
        cursor.close();
        db.close();
        return habits;
    }

    public void deleteAllHabits() {
        SQLiteDatabase db = dbHelper.getWritableDatabase();
        db.delete(HabitContract.HabitEntry.TABLE_NAME, null, null);
        db.close();
    }
}
