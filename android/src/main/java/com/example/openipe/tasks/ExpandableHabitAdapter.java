package com.example.openipe.tasks;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.CheckBox;

import androidx.recyclerview.widget.RecyclerView;

import com.example.openipe.R;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class ExpandableHabitAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder> {

    private static final int VIEW_TYPE_STACK = 0;
    private static final int VIEW_TYPE_HABIT = 1;

    private List<Task> habitList;
    private Map<String, Boolean> expandStateMap;
    private Context context;
    private List<Object> displayList;
    private HabitDbHandler dbHandler;

    public ExpandableHabitAdapter(Context context, List<Task> habitList, HabitDbHandler dbHandler) {
        this.context = context;
        this.habitList = habitList;
        this.dbHandler = dbHandler;
        this.expandStateMap = new HashMap<>();
        for (Task habit : habitList) {
            if (!expandStateMap.containsKey(habit.getContext())) {
                expandStateMap.put(habit.getContext(), false);
            }
        }
        generateDisplayList();
    }

    private void generateDisplayList() {
        displayList = new ArrayList<>();
        String lastStack = "";
        for (Task habit : habitList) {
            if (!habit.getContext().equals(lastStack)) {
                displayList.add(habit.getContext());
                lastStack = habit.getContext();
            }
            Boolean isExpanded = expandStateMap.get(habit.getContext());
            if (isExpanded == null) {
                isExpanded = false;
                expandStateMap.put(habit.getContext(), false);
            }
            if (isExpanded && !habit.getIsCompleted()) {
                displayList.add(habit);
            }
        }
    }

    @Override
    public int getItemViewType(int position) {
        if (displayList.get(position) instanceof String) {
            return VIEW_TYPE_STACK;
        } else {
            return VIEW_TYPE_HABIT;
        }
    }

    @Override
    public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
        LayoutInflater inflater = LayoutInflater.from(context);
        if (viewType == VIEW_TYPE_STACK) {
            View view = inflater.inflate(R.layout.habits_item_habit_stack, parent, false);
            return new StackViewHolder(view);
        } else {
            View view = inflater.inflate(R.layout.habits_item_habit, parent, false);
            return new HabitViewHolder(view);
        }
    }

    @Override
    public void onBindViewHolder(RecyclerView.ViewHolder holder, int position) {
        if (getItemViewType(position) == VIEW_TYPE_STACK) {
            StackViewHolder stackViewHolder = (StackViewHolder) holder;
            String stackName = (String) displayList.get(position);
            Boolean isExpanded = expandStateMap.get(stackName);
            stackViewHolder.bind(stackName, isExpanded, new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    Boolean currentExpandedState = expandStateMap.get(stackName);
                    expandStateMap.put(stackName, currentExpandedState == null || !currentExpandedState);
                    generateDisplayList();
                    notifyDataSetChanged();
                }
            });
        } else {
            HabitViewHolder habitViewHolder = (HabitViewHolder) holder;
            Task habit = (Task) displayList.get(position);
            habitViewHolder.bind(habit, new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    CheckBox checkBox = (CheckBox) v;
                    habit.setIsCompleted(checkBox.isChecked());
                    dbHandler.updateHabit(habit);
                    generateDisplayList();
                    notifyDataSetChanged();
                }
            });
        }
    }

    @Override
    public int getItemCount() {
        return displayList.size();
    }

    public void setHabits(List<Task> habits) {
        this.habitList = habits;
        generateDisplayList();
        notifyDataSetChanged();
    }

    public void addHabit(Task habit) {
        this.habitList.add(habit);
        if (!expandStateMap.containsKey(habit.getContext())) {
            expandStateMap.put(habit.getContext(), false);
        }
        generateDisplayList();
        notifyDataSetChanged();
    }
}
