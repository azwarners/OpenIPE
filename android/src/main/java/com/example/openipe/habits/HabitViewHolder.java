package com.example.openipe.habits;

import android.view.View;
import android.widget.CheckBox;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import com.example.openipe.R;

public class HabitViewHolder extends RecyclerView.ViewHolder {
    TextView habitName;
    CheckBox habitCheckBox;

    public HabitViewHolder(View itemView) {
        super(itemView);
        habitName = itemView.findViewById(R.id.textDescription);
        habitCheckBox = itemView.findViewById(R.id.checkBoxCompleted);
    }
}
