package com.example.openipe.tasks;

import android.view.View;
import android.widget.CheckBox;
import android.widget.TextView;

import androidx.recyclerview.widget.RecyclerView;

import com.example.openipe.R;

public class HabitViewHolder extends RecyclerView.ViewHolder {
    TextView description;
    CheckBox checkBoxCompleted;

    public HabitViewHolder(View itemView) {
        super(itemView);
        description = itemView.findViewById(R.id.textDescription);
        checkBoxCompleted = itemView.findViewById(R.id.checkBoxCompleted);
    }

    void bind(Task habit, View.OnClickListener clickListener) {
        description.setText(habit.getDescription());
        checkBoxCompleted.setChecked(habit.getIsCompleted());
        checkBoxCompleted.setOnClickListener(clickListener);
    }
}
