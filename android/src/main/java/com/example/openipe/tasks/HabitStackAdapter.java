package com.example.openipe.tasks;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.recyclerview.widget.RecyclerView;

import com.example.openipe.R;

import java.util.List;

public class HabitStackAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder> {
    private List<HabitStack> habitStackList;

    public HabitStackAdapter(List<HabitStack> habitStackList) {
        this.habitStackList = habitStackList;
    }

    @Override
    public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.habits_item_habit_stack, parent, false);
        return new StackViewHolder(view);
    }

    @Override
    public void onBindViewHolder(RecyclerView.ViewHolder holder, int position) {
        HabitStack stack = habitStackList.get(position);
        StackViewHolder stackHolder = (StackViewHolder) holder;
        stackHolder.stackName.setText(stack.getName());
        // Handle expand/collapse logic here
    }

    @Override
    public int getItemCount() {
        return habitStackList.size();
    }

    public class StackViewHolder extends RecyclerView.ViewHolder {
        TextView stackName;

        public StackViewHolder(View itemView) {
            super(itemView);
            stackName = itemView.findViewById(R.id.textStackName);
            itemView.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    // Toggle expansion logic
                }
            });
        }
    }
}
