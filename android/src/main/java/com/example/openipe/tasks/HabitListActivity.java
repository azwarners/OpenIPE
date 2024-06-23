package com.example.openipe.tasks;

import android.content.Intent;
import android.os.Bundle;
import android.widget.TextView;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.example.openipe.R;
import com.google.android.material.floatingactionbutton.FloatingActionButton;

import java.util.ArrayList;
import java.util.List;

public class HabitListActivity extends AppCompatActivity {

    private RecyclerView recyclerView;
    private ExpandableHabitAdapter habitAdapter;
    private List<Task> habitList = new ArrayList<>();
    private ActivityResultLauncher<Intent> addHabitActivityResultLauncher;
    private HabitDbHandler dbHandler;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.habits_activity_habit_list);

        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        // Inflate the custom title layout
        getSupportActionBar().setDisplayShowTitleEnabled(false);
        getLayoutInflater().inflate(R.layout.toolbar_title, toolbar);

        TextView toolbarTitle = toolbar.findViewById(R.id.toolbar_title);
        toolbarTitle.setText(R.string.habit_list_title); // Assuming you have a string resource for the title

        dbHandler = new HabitDbHandler(this);

        recyclerView = findViewById(R.id.recyclerView);
        recyclerView.setLayoutManager(new LinearLayoutManager(this));
        habitAdapter = new ExpandableHabitAdapter(this, habitList, dbHandler);
        recyclerView.setAdapter(habitAdapter);

        // Load habits from the database
        loadHabits();

        addHabitActivityResultLauncher = registerForActivityResult(
                new ActivityResultContracts.StartActivityForResult(),
                result -> {
                    if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                        Intent data = result.getData();
                        String description = data.getStringExtra("DESCRIPTION");
                        String stack = data.getStringExtra("STACK");
                        String recurrence = data.getStringExtra("RECURRENCE");
                        Task newHabit = new Task(description, recurrence, stack, System.currentTimeMillis(), false);
                        dbHandler.addHabit(newHabit);
                        habitAdapter.addHabit(newHabit);
                    }
                }
        );

        FloatingActionButton addHabitButton = findViewById(R.id.addHabitButton);
        addHabitButton.setOnClickListener(v -> {
            Intent intent = new Intent(HabitListActivity.this, AddHabitActivity.class);
            addHabitActivityResultLauncher.launch(intent);
        });
    }

    private void loadHabits() {
        habitList = dbHandler.getAllHabits();
        habitAdapter.setHabits(habitList);
    }
}
