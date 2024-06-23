package com.example.openipe;

public class MenuItem {
    private int iconResId; // Resource ID for the icon
    private String text; // Text for the menu item
    private String contentDescription;  // Content description for accessibility
    private String packageName;  // This is for launching the intent from the menu

    public MenuItem(int iconResId, String text, String contentDescription, String packageName) {
        this.iconResId = iconResId;
        this.text = text;
        this.contentDescription = contentDescription;
        this.packageName = packageName;
    }

    public int getIconResId() {
        return iconResId;
    }

    public String getText() {
        return text;
    }

    public String getContentDescription() {
        return contentDescription;
    }

    public String getPackageName() {
        return packageName;
    }

}
