package com.example.openipe.tasks;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;

import androidx.appcompat.app.AppCompatActivity;

import com.example.openipe.R;

public class AddHabitActivity extends AppCompatActivity {

    private EditText editTextDescription, editTextStack, editTextRecurrence;
    private Button buttonSubmit;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.habits_activity_add_habit);

        editTextDescription = findViewById(R.id.editTextHabitDescription);
        editTextStack = findViewById(R.id.editTextHabitStack);
        editTextRecurrence = findViewById(R.id.editTextRecurrence);
        buttonSubmit = findViewById(R.id.buttonSubmitHabit);

        buttonSubmit.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String description = editTextDescription.getText().toString();
                String stack = editTextStack.getText().toString();
                String recurrence = editTextRecurrence.getText().toString();

                Intent resultIntent = new Intent();
                resultIntent.putExtra("DESCRIPTION", description);
                resultIntent.putExtra("STACK", stack);
                resultIntent.putExtra("RECURRENCE", recurrence);
                setResult(Activity.RESULT_OK, resultIntent);
                finish();
            }
        });
    }
}
