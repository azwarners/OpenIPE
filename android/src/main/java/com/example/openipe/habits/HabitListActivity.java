package com.example.openipe.habits;

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
import com.example.openipe.core.habits.Habit;
import com.example.openipe.core.habits.HabitStack;
import com.google.android.material.floatingactionbutton.FloatingActionButton;

import java.util.ArrayList;
import java.util.List;

public class HabitListActivity extends AppCompatActivity {

    private RecyclerView recyclerView;
    private HabitStackAdapter habitAdapter;
    private List<Habit> habitList = new ArrayList<>();
    private List<HabitStack> habitStackList = new ArrayList<>();
    private ActivityResultLauncher<Intent> addHabitActivityResultLauncher;
    private HabitDbHelper dbHelper;

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

        dbHelper = new HabitDbHelper(this);

        recyclerView = findViewById(R.id.recyclerView);
        recyclerView.setLayoutManager(new LinearLayoutManager(this));
        habitAdapter = new HabitStackAdapter(this, habitList, habitStackList, dbHelper);
        recyclerView.setAdapter(habitAdapter);

        // Load habits and habit stacks from the database
        loadHabitsAndStacks();

        addHabitActivityResultLauncher = registerForActivityResult(
                new ActivityResultContracts.StartActivityForResult(),
                result -> {
                    if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                        Intent data = result.getData();
                        String description = data.getStringExtra("DESCRIPTION");
                        String stack = data.getStringExtra("STACK");
                        String recurrence = data.getStringExtra("RECURRENCE");
                        // Use 0 as a temporary ID for new habits
                        Habit newHabit = new Habit(0, description, recurrence, stack, System.currentTimeMillis(), false);
                        dbHelper.addHabit(newHabit);
                        updateHabitsAndStacks();
                    }
                }
        );

        FloatingActionButton addHabitButton = findViewById(R.id.addHabitButton);
        addHabitButton.setOnClickListener(v -> {
            Intent intent = new Intent(HabitListActivity.this, AddHabitActivity.class);
            addHabitActivityResultLauncher.launch(intent);
        });
    }

    private void loadHabitsAndStacks() {
        try {
            habitList = dbHelper.getAllHabits();
            habitStackList = dbHelper.getAllHabitStacks();
            habitAdapter.updateHabitList(habitList);
            habitAdapter.updateHabitStackList(habitStackList);
        } catch (Exception e) {
            // Handle error
        }
    }

    private void updateHabitsAndStacks() {
        habitList = dbHelper.getAllHabits();
        habitStackList = dbHelper.getAllHabitStacks();
        habitAdapter.updateHabitList(habitList);
        habitAdapter.updateHabitStackList(habitStackList);
    }
}
