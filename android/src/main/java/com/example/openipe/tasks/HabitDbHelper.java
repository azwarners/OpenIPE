package com.example.openipe.tasks;

import android.content.Context;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

public class HabitDbHelper extends SQLiteOpenHelper {

    private static final String DATABASE_NAME = "Habits.db";
    private static final int DATABASE_VERSION = 1;

    public HabitDbHelper(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        final String SQL_CREATE_HABIT_TABLE = "CREATE TABLE " + HabitContract.HabitEntry.TABLE_NAME + " (" +
                HabitContract.HabitEntry._ID + " INTEGER PRIMARY KEY AUTOINCREMENT," +
                HabitContract.HabitEntry.COLUMN_DESCRIPTION + " TEXT NOT NULL, " +
                HabitContract.HabitEntry.COLUMN_RECURRENCE + " TEXT, " +
                HabitContract.HabitEntry.COLUMN_STACK_NAME + " TEXT, " +
                HabitContract.HabitEntry.COLUMN_DUE_TIMESTAMP + " INTEGER, " +
                HabitContract.HabitEntry.COLUMN_IS_COMPLETED + " INTEGER);";

        final String SQL_CREATE_HISTORY_TABLE = "CREATE TABLE " + HabitContract.HistoryEntry.TABLE_NAME + " (" +
                HabitContract.HistoryEntry._ID + " INTEGER PRIMARY KEY AUTOINCREMENT," +
                HabitContract.HistoryEntry.COLUMN_HABIT_ID + " INTEGER NOT NULL, " +
                HabitContract.HistoryEntry.COLUMN_COMPLETION_TIMESTAMP + " INTEGER, " +
                "FOREIGN KEY (" + HabitContract.HistoryEntry.COLUMN_HABIT_ID + ") REFERENCES " +
                HabitContract.HabitEntry.TABLE_NAME + " (" + HabitContract.HabitEntry._ID + ") ON DELETE CASCADE);";

        db.execSQL(SQL_CREATE_HABIT_TABLE);
        db.execSQL(SQL_CREATE_HISTORY_TABLE);
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        db.execSQL("DROP TABLE IF EXISTS " + HabitContract.HabitEntry.TABLE_NAME);
        db.execSQL("DROP TABLE IF EXISTS " + HabitContract.HistoryEntry.TABLE_NAME);
        onCreate(db);
    }
}
