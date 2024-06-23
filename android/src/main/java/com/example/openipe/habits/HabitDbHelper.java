package com.example.openipe.habits;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.util.Log;

import com.example.openipe.core.habits.Habit;
import com.example.openipe.core.habits.HabitRepository;
import com.example.openipe.core.habits.HabitSchema;
import com.example.openipe.core.habits.HabitStack;

import java.util.ArrayList;
import java.util.List;

public class HabitDbHelper extends SQLiteOpenHelper implements HabitRepository {

    private static final String TAG = "HabitDbHelper";
    private static final String DATABASE_NAME = "Habits.db";
    private static final int DATABASE_VERSION = 1;

    public HabitDbHelper(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        final String SQL_CREATE_HABIT_TABLE = "CREATE TABLE " + HabitSchema.HabitEntry.TABLE_NAME + " (" +
                HabitSchema.HabitEntry._ID + " INTEGER PRIMARY KEY AUTOINCREMENT," +
                HabitSchema.HabitEntry.COLUMN_DESCRIPTION + " TEXT NOT NULL, " +
                HabitSchema.HabitEntry.COLUMN_RECURRENCE + " TEXT, " +
                HabitSchema.HabitEntry.COLUMN_STACK_NAME + " TEXT, " +
                HabitSchema.HabitEntry.COLUMN_DUE_TIMESTAMP + " INTEGER, " +
                HabitSchema.HabitEntry.COLUMN_IS_COMPLETED + " INTEGER);";

        final String SQL_CREATE_HISTORY_TABLE = "CREATE TABLE " + HabitSchema.HistoryEntry.TABLE_NAME + " (" +
                HabitSchema.HistoryEntry._ID + " INTEGER PRIMARY KEY AUTOINCREMENT," +
                HabitSchema.HistoryEntry.COLUMN_HABIT_ID + " INTEGER NOT NULL, " +
                HabitSchema.HistoryEntry.COLUMN_COMPLETION_TIMESTAMP + " INTEGER, " +
                "FOREIGN KEY (" + HabitSchema.HistoryEntry.COLUMN_HABIT_ID + ") REFERENCES " +
                HabitSchema.HabitEntry.TABLE_NAME + " (" + HabitSchema.HabitEntry._ID + ") ON DELETE CASCADE);";

        db.execSQL(SQL_CREATE_HABIT_TABLE);
        db.execSQL(SQL_CREATE_HISTORY_TABLE);
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        db.execSQL("DROP TABLE IF EXISTS " + HabitSchema.HabitEntry.TABLE_NAME);
        db.execSQL("DROP TABLE IF EXISTS " + HabitSchema.HistoryEntry.TABLE_NAME);
        onCreate(db);
    }

    @Override
    public void addHabit(Habit habit) {
        SQLiteDatabase db = this.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put(HabitSchema.HabitEntry.COLUMN_DESCRIPTION, habit.getDescription());
        values.put(HabitSchema.HabitEntry.COLUMN_RECURRENCE, habit.getRecurrence());
        values.put(HabitSchema.HabitEntry.COLUMN_STACK_NAME, habit.getStackName());
        values.put(HabitSchema.HabitEntry.COLUMN_DUE_TIMESTAMP, habit.getDueTimestamp());
        values.put(HabitSchema.HabitEntry.COLUMN_IS_COMPLETED, habit.getIsCompleted() ? 1 : 0);
        db.insert(HabitSchema.HabitEntry.TABLE_NAME, null, values);
        db.close();
    }

    @Override
    public void updateHabit(Habit habit) {
        SQLiteDatabase db = this.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put(HabitSchema.HabitEntry.COLUMN_DESCRIPTION, habit.getDescription());
        values.put(HabitSchema.HabitEntry.COLUMN_RECURRENCE, habit.getRecurrence());
        values.put(HabitSchema.HabitEntry.COLUMN_STACK_NAME, habit.getStackName());
        values.put(HabitSchema.HabitEntry.COLUMN_DUE_TIMESTAMP, habit.getDueTimestamp());
        values.put(HabitSchema.HabitEntry.COLUMN_IS_COMPLETED, habit.getIsCompleted() ? 1 : 0);

        String selection = HabitSchema.HabitEntry._ID + " = ?";
        String[] selectionArgs = { String.valueOf(habit.getId()) };

        db.update(HabitSchema.HabitEntry.TABLE_NAME, values, selection, selectionArgs);
        db.close();
    }

    @Override
    public List<Habit> getAllHabits() {
        List<Habit> habits = new ArrayList<>();
        SQLiteDatabase db = this.getReadableDatabase();
        Cursor cursor = db.query(HabitSchema.HabitEntry.TABLE_NAME, null, null, null, null, null, null);
        if (cursor.moveToFirst()) {
            do {
                long id = cursor.getLong(cursor.getColumnIndex(HabitSchema.HabitEntry._ID));
                String description = cursor.getString(cursor.getColumnIndex(HabitSchema.HabitEntry.COLUMN_DESCRIPTION));
                String recurrence = cursor.getString(cursor.getColumnIndex(HabitSchema.HabitEntry.COLUMN_RECURRENCE));
                String stackName = cursor.getString(cursor.getColumnIndex(HabitSchema.HabitEntry.COLUMN_STACK_NAME));
                long dueTimestamp = cursor.getLong(cursor.getColumnIndex(HabitSchema.HabitEntry.COLUMN_DUE_TIMESTAMP));
                boolean isCompleted = cursor.getInt(cursor.getColumnIndex(HabitSchema.HabitEntry.COLUMN_IS_COMPLETED)) == 1;
                Habit habit = new Habit(id, description, recurrence, stackName, dueTimestamp, isCompleted);
                habits.add(habit);
            } while (cursor.moveToNext());
        }
        cursor.close();
        db.close();
        return habits;
    }

    @Override
    public List<HabitStack> getAllHabitStacks() {
        List<HabitStack> habitStacks = new ArrayList<>();
        String selectQuery = "SELECT DISTINCT " + HabitSchema.HabitEntry.COLUMN_STACK_NAME + " FROM " + HabitSchema.HabitEntry.TABLE_NAME;
        SQLiteDatabase db = this.getReadableDatabase();
        Cursor cursor = db.rawQuery(selectQuery, null);

        if (cursor.moveToFirst()) {
            do {
                String stackName = cursor.getString(cursor.getColumnIndex(HabitSchema.HabitEntry.COLUMN_STACK_NAME));
                List<Habit> habits = getHabitsByStack(stackName);
                HabitStack stack = new HabitStack(stackName, habits);
                habitStacks.add(stack);
            } while (cursor.moveToNext());
        }
        cursor.close();
        db.close();
        return habitStacks;
    }

    private List<Habit> getHabitsByStack(String stackName) {
        List<Habit> habitList = new ArrayList<>();
        String selectQuery = "SELECT * FROM " + HabitSchema.HabitEntry.TABLE_NAME + " WHERE " + HabitSchema.HabitEntry.COLUMN_STACK_NAME + " = ?";
        SQLiteDatabase db = this.getReadableDatabase();
        Cursor cursor = db.rawQuery(selectQuery, new String[]{stackName});

        if (cursor.moveToFirst()) {
            do {
                long id = cursor.getLong(cursor.getColumnIndex(HabitSchema.HabitEntry._ID));
                String description = cursor.getString(cursor.getColumnIndex(HabitSchema.HabitEntry.COLUMN_DESCRIPTION));
                String recurrence = cursor.getString(cursor.getColumnIndex(HabitSchema.HabitEntry.COLUMN_RECURRENCE));
                String stackNameColumn = cursor.getString(cursor.getColumnIndex(HabitSchema.HabitEntry.COLUMN_STACK_NAME));
                long dueTimestamp = cursor.getLong(cursor.getColumnIndex(HabitSchema.HabitEntry.COLUMN_DUE_TIMESTAMP));
                boolean isCompleted = cursor.getInt(cursor.getColumnIndex(HabitSchema.HabitEntry.COLUMN_IS_COMPLETED)) == 1;
                Habit habit = new Habit(id, description, recurrence, stackNameColumn, dueTimestamp, isCompleted);
                habitList.add(habit);
            } while (cursor.moveToNext());
        }
        cursor.close();
        db.close();
        return habitList;
    }

    @Override
    public void deleteAllHabits() {
        SQLiteDatabase db = this.getWritableDatabase();
        db.delete(HabitSchema.HabitEntry.TABLE_NAME, null, null);
        db.close();
    }
}
