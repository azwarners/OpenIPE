package com.example.openipe.habits;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import androidx.recyclerview.widget.RecyclerView;
import com.example.openipe.R;
import com.example.openipe.core.habits.Habit;
import com.example.openipe.core.habits.HabitStack;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class HabitStackAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder> {

    private static final int VIEW_TYPE_STACK = 0;
    private static final int VIEW_TYPE_HABIT = 1;

    private List<Habit> habitList;
    private List<HabitStack> habitStackList;
    private Map<String, Boolean> expandStateMap;
    private Context context;
    private List<Object> displayList;
    private HabitDbHelper dbHelper;

    public HabitStackAdapter(Context context, List<Habit> habitList, List<HabitStack> habitStackList, HabitDbHelper dbHelper) {
        this.context = context;
        this.habitList = habitList;
        this.habitStackList = habitStackList;
        this.dbHelper = dbHelper;
        this.expandStateMap = new HashMap<>();
        for (HabitStack stack : habitStackList) {
            expandStateMap.put(stack.getName(), false);
        }
        generateDisplayList();
    }

    private void generateDisplayList() {
        displayList = new ArrayList<>();
        for (HabitStack stack : habitStackList) {
            displayList.add(stack);
            Boolean isExpanded = expandStateMap.get(stack.getName());
            if (isExpanded == null) {
                isExpanded = false;
                expandStateMap.put(stack.getName(), false);
            }
            if (isExpanded) {
                for (Habit habit : habitList) {
                    if (habit.getStackName().equals(stack.getName()) && !habit.getIsCompleted()) {
                        displayList.add(habit);
                    }
                }
            }
        }
    }

    @Override
    public int getItemViewType(int position) {
        return displayList.get(position) instanceof HabitStack ? VIEW_TYPE_STACK : VIEW_TYPE_HABIT;
    }

    @Override
    public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
        if (viewType == VIEW_TYPE_STACK) {
            View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.habits_item_habit_stack, parent, false);
            return new StackViewHolder(view);
        } else {
            View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.habits_item_habit, parent, false);
            return new HabitViewHolder(view);
        }
    }

    @Override
    public void onBindViewHolder(RecyclerView.ViewHolder holder, int position) {
        if (getItemViewType(position) == VIEW_TYPE_STACK) {
            HabitStack stack = (HabitStack) displayList.get(position);
            StackViewHolder stackHolder = (StackViewHolder) holder;
            stackHolder.stackName.setText(stack.getName());
            View.OnClickListener toggleExpandCollapse = v -> {
                boolean isExpanded = expandStateMap.get(stack.getName());
                expandStateMap.put(stack.getName(), !isExpanded);
                generateDisplayList();
                notifyDataSetChanged();
            };
            stackHolder.expandIcon.setOnClickListener(toggleExpandCollapse);
            stackHolder.itemView.setOnClickListener(toggleExpandCollapse);
        } else {
            Habit habit = (Habit) displayList.get(position);
            HabitViewHolder habitHolder = (HabitViewHolder) holder;
            habitHolder.habitName.setText(habit.getDescription());
            habitHolder.habitCheckBox.setChecked(habit.getIsCompleted());
        }
    }

    @Override
    public int getItemCount() {
        return displayList.size();
    }

    public void updateHabitList(List<Habit> habitList) {
        this.habitList = habitList;
        generateDisplayList();
        notifyDataSetChanged();
    }

    public void updateHabitStackList(List<HabitStack> habitStackList) {
        this.habitStackList = habitStackList;
        generateDisplayList();
        notifyDataSetChanged();
    }
}
