/*
 * @(#)AbstractApplication.java
 *
 * Copyright (c) 1996-2009 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.app;

import java.awt.*;
import org.jhotdraw.beans.*;
import org.jhotdraw.gui.Worker;
import org.jhotdraw.util.*;
import java.util.*;
import java.util.prefs.*;
import javax.swing.*;
import java.io.*;
import org.jhotdraw.util.prefs.PreferencesUtil;

/**
 * This abstract class can be extended to implement an {@link Application}.
 *
 * @author Werner Randelshofer
 * @version $Id: AbstractApplication.java 529 2009-06-08 21:12:23Z rawcoder $
 */
public abstract class AbstractApplication extends AbstractBean implements Application {

    private LinkedList<View> views = new LinkedList<View>();
    private Collection<View> unmodifiableViews;
    private boolean isEnabled = true;
    protected ResourceBundleUtil labels;
    private ApplicationModel model;
    private LinkedList<File> recentFiles = new LinkedList<File>();
    private final static int maxRecentFilesCount = 10;
    private Preferences prefs;
    private View activeView;
    public final static String VIEW_COUNT_PROPERTY = "viewCount";

    /** Creates a new instance. */
    public AbstractApplication() {
    }

    public void init() {
        prefs = PreferencesUtil.userNodeForPackage((getModel() == null) ? getClass() : getModel().getClass());

        int count = prefs.getInt("recentFileCount", 0);
        for (int i = 0; i < count; i++) {
            String path = prefs.get("recentFile." + i, null);
            if (path != null) {
                recentFiles.add(new File(path));
            }
        }

        if (model != null) {
            model.initApplication(this);
        }
    }

    public void start() {
        final View p = createView();
        add(p);
        p.setEnabled(false);
        show(p);
        p.execute(new Worker() {

            public Object construct() {
                p.clear();
                return null;
            }

            public void finished(Object result) {
                p.setEnabled(true);
            }
        });
    }

    public final View createView() {
        View p = basicCreateView();
        p.init();
        if (getModel() != null) {
            getModel().initView(this, p);
        }
        initViewActions(p);
        return p;
    }

    public void setModel(ApplicationModel newValue) {
        ApplicationModel oldValue = model;
        model = newValue;
        firePropertyChange("model", oldValue, newValue);
    }

    public ApplicationModel getModel() {
        return model;
    }

    protected View basicCreateView() {
        return model.createView();
    }

    /**
     * Sets the active view. Calls deactivate on the previously
     * active view, and then calls activate on the given view.
     * 
     * @param newValue Active view, can be null.
     */
    public void setActiveView(View newValue) {
        View oldValue = activeView;
        if (activeView != null) {
            activeView.deactivate();
        }
        activeView = newValue;
        if (activeView != null) {
            activeView.activate();
        }
        firePropertyChange(ACTIVE_VIEW_PROPERTY, oldValue, newValue);
    }

    /**
     * Gets the active view.
     * 
     * @return The active view, can be null.
     */
    public View getActiveView() {
        if (activeView == null && views.size() > 0) {
            return views.getLast();
        }
        return activeView;
    }

    public String getName() {
        return model.getName();
    }

    public String getVersion() {
        return model.getVersion();
    }

    public String getCopyright() {
        return model.getCopyright();
    }

    protected abstract void initViewActions(View p);

    public void stop() {
        for (View p : new LinkedList<View>(views())) {
            dispose(p);
        }
        System.exit(0);
    }

    public void remove(View p) {
        if (p == activeView) {
            setActiveView(null);
        }
        hide(p);
        int oldCount = views.size();
        views.remove(p);
        p.setApplication(null);
        firePropertyChange(VIEW_COUNT_PROPERTY, oldCount, views.size());
    }

    public void add(View p) {
        if (p.getApplication() != this) {
            int oldCount = views.size();
            views.add(p);
            p.setApplication(this);
            firePropertyChange(VIEW_COUNT_PROPERTY, oldCount, views.size());
        }
    }

    public void dispose(View view) {
        remove(view);
        view.dispose();
    }

    public Collection<View> views() {
        if (unmodifiableViews == null) {
            unmodifiableViews = Collections.unmodifiableCollection(views);
        }
        return unmodifiableViews;
    }

    public boolean isEnabled() {
        return isEnabled;
    }

    public void setEnabled(boolean newValue) {
        boolean oldValue = isEnabled;
        isEnabled = newValue;
        firePropertyChange("enabled", oldValue, newValue);
    }

    public Container createContainer() {
        return new JFrame();
    }

    public void launch(String[] args) {
        configure(args);
        SwingUtilities.invokeLater(new Runnable() {

            public void run() {
                init();
                start();
            }
        });
    }

    protected void initLabels() {
        labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
    }

    public void configure(String[] args) {
    }

    public java.util.List<File> recentFiles() {
        return Collections.unmodifiableList(recentFiles);
    }

    public void clearRecentFiles() {
        @SuppressWarnings("unchecked")
        java.util.List<File> oldValue = (java.util.List<File>) recentFiles.clone();
        recentFiles.clear();
        prefs.putInt("recentFileCount", recentFiles.size());
        firePropertyChange("recentFiles",
                Collections.unmodifiableList(oldValue),
                Collections.unmodifiableList(recentFiles));
    }

    public void addRecentFile(File file) {
        @SuppressWarnings("unchecked")
        java.util.List<File> oldValue = (java.util.List<File>) recentFiles.clone();
        if (recentFiles.contains(file)) {
            recentFiles.remove(file);
        }
        recentFiles.addFirst(file);
        if (recentFiles.size() > maxRecentFilesCount) {
            recentFiles.removeLast();
        }

        prefs.putInt("recentFileCount", recentFiles.size());
        int i = 0;
        for (File f : recentFiles) {
            prefs.put("recentFile." + i, f.getPath());
            i++;
        }

        firePropertyChange("recentFiles", oldValue, 0);
        firePropertyChange("recentFiles",
                Collections.unmodifiableList(oldValue),
                Collections.unmodifiableList(recentFiles));
    }

    public void removePalette(Window palette) {
    }

    public void addPalette(Window palette) {
    }

    public void removeWindow(Window window) {
    }

    public void addWindow(Window window, View p) {
    }
}
