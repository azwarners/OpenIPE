package com.example.openipe.habits;

import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import com.example.openipe.R;

public class StackViewHolder extends RecyclerView.ViewHolder {
    TextView stackName;
    ImageView expandIcon;

    public StackViewHolder(View itemView) {
        super(itemView);
        stackName = itemView.findViewById(R.id.textStackName);
        expandIcon = itemView.findViewById(R.id.expandIcon);
    }
}
