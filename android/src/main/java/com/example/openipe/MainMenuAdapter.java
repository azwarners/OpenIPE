package com.example.openipe;

import android.content.Context;
import android.content.Intent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.example.openipe.habits.HabitListActivity;

import java.util.List;

public class MainMenuAdapter extends RecyclerView.Adapter<MainMenuAdapter.MenuItemViewHolder> {
    private List<MenuItem> menuItems;
    private Context context;  // Pass context to use it for launching intents

    public MainMenuAdapter(List<MenuItem> menuItems, Context context) {
        this.menuItems = menuItems;
        this.context = context;
    }

    @NonNull
    @Override
    public MenuItemViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.main_menu_item_layout, parent, false);
        return new MenuItemViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull MenuItemViewHolder holder, int position) {
        MenuItem menuItem = menuItems.get(position);
        holder.itemView.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (menuItem.getPackageName().equals("com.example.openipe.habits")) {
                    Intent intent = new Intent(context, HabitListActivity.class);
                    context.startActivity(intent);
                }
            }
        });
        holder.imageView.setImageResource(menuItem.getIconResId());
        holder.imageView.setContentDescription(menuItem.getContentDescription());
        holder.textView.setText(menuItem.getText());
    }

    @Override
    public int getItemCount() {
        return menuItems.size();
    }

    public static class MenuItemViewHolder extends RecyclerView.ViewHolder {
        ImageView imageView;
        TextView textView;

        public MenuItemViewHolder(View itemView) {
            super(itemView);
            imageView = itemView.findViewById(R.id.image_view);
            textView = itemView.findViewById(R.id.mainMenuItemTextView);
        }
    }

}
