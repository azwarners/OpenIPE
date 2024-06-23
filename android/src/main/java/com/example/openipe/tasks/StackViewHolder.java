package com.example.openipe.tasks;

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

    void bind(String stack, boolean isExpanded, View.OnClickListener clickListener) {
        stackName.setText(stack);
        expandIcon.setImageResource(isExpanded ? R.drawable.ic_expand_less : R.drawable.ic_expand_more);
        itemView.setOnClickListener(clickListener);
    }
}
