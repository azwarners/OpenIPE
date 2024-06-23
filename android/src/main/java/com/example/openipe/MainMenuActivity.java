package com.example.openipe;

import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.widget.TextView;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.core.content.ContextCompat;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.recyclerview.widget.DividerItemDecoration;
import androidx.recyclerview.widget.GridLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import java.util.ArrayList;
import java.util.List;

public class MainMenuActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main_menu);

        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        // Disable the default title if you haven't already
        getSupportActionBar().setDisplayShowTitleEnabled(false);

        // Find the TextView and set its text
        TextView toolbarTitle = findViewById(R.id.toolbar_title);
        toolbarTitle.setText("OpenIPE");


        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        RecyclerView mainMenuRecyclerView = findViewById(R.id.mainMenuRecyclerView);

        // List of menu items to be displayed in the RecyclerView
        List<MenuItem> menuItems = new ArrayList<>();
        menuItems.add(new MenuItem(R.drawable.ic_habit_icon, "Habit List", "Open habit list", "com.example.openipe.habits"));
        menuItems.add(new MenuItem(R.drawable.ic_calendar_icon, "Calendar", "Open calendar", "package"));
        menuItems.add(new MenuItem(R.drawable.ic_task_icon, "Task List", "Open task list", "package"));
        menuItems.add(new MenuItem(R.drawable.ic_notepad_icon, "Notepad", "Open notepad", "package"));
        menuItems.add(new MenuItem(R.drawable.ic_project_icon, "Project List", "Open project list", "package"));
        menuItems.add(new MenuItem(R.drawable.ic_goal_icon, "Goal List", "Open goal list", "package"));
        menuItems.add(new MenuItem(R.drawable.ic_timetracker_icon, "Time Tracker", "Open time tracker", "package"));

        MainMenuAdapter adapter = new MainMenuAdapter(menuItems, this);
        mainMenuRecyclerView.setAdapter(adapter);

        int numberOfColumns = 1; // Adjust the number of columns based on your needs
        GridLayoutManager gridLayoutManager = new GridLayoutManager(this, numberOfColumns);
        mainMenuRecyclerView.setLayoutManager(gridLayoutManager);

        DividerItemDecoration dividerItemDecoration = new DividerItemDecoration(mainMenuRecyclerView.getContext(), gridLayoutManager.getOrientation());
        Drawable drawable = ContextCompat.getDrawable(getApplicationContext(), R.drawable.divider);
        dividerItemDecoration.setDrawable(drawable);
        mainMenuRecyclerView.addItemDecoration(dividerItemDecoration);
    }

}
