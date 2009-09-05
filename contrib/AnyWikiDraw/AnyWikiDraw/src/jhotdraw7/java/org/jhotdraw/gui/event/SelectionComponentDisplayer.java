/**
 * @(#)SelectionComponentDisplayer.java
 *
 * Copyright (c) 2006-2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.gui.event;

import java.awt.Dimension;
import java.beans.*;
import java.lang.ref.WeakReference;
import javax.swing.*;
import org.jhotdraw.draw.*;

/**
 * Calls setVisible(true/false) on components, which show attributes of the 
 * drawing editor and of its views based on the current selection.
 * <p>
 * Holds a {@code WeakReference} on the component. Automatically disposes
 * itself if the component no longer exists.
 *
 * @author Werner Randelshofer
 * @version $Id: SelectionComponentDisplayer.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class SelectionComponentDisplayer
        implements PropertyChangeListener, FigureSelectionListener {

    protected DrawingView view;
    protected DrawingEditor editor;
    protected WeakReference<JComponent> weakRef;
    protected int minSelectionCount = 1;
    protected boolean isVisibleIfCreationTool = true;

    public SelectionComponentDisplayer(DrawingEditor editor, JComponent component) {
        this.editor = editor;
        this.weakRef = new WeakReference<JComponent>(component);
        if (editor.getActiveView() != null) {
            view = editor.getActiveView();
            view.addPropertyChangeListener(this);
            view.addFigureSelectionListener(this);
        }
        editor.addPropertyChangeListener(this);
        updateVisibility();
    }

    public void propertyChange(PropertyChangeEvent evt) {
        String name = evt.getPropertyName();
        if (name == DrawingEditor.ACTIVE_VIEW_PROPERTY) {
            if (view != null) {
                view.removePropertyChangeListener(this);
                view.removeFigureSelectionListener(this);
            }
            view = (DrawingView) evt.getNewValue();
            if (view != null) {
                view.addPropertyChangeListener(this);
                view.addFigureSelectionListener(this);
            }
            updateVisibility();
        } else if (name == DrawingEditor.TOOL_PROPERTY) {
            updateVisibility();
        }
    }

    public void selectionChanged(FigureSelectionEvent evt) {
        updateVisibility();
    }

    public void updateVisibility() {
        boolean newValue = editor != null &&
                editor.getActiveView() != null &&
                (isVisibleIfCreationTool && editor.getTool() != null && !(editor.getTool() instanceof SelectionTool) ||
                editor.getActiveView().getSelectionCount() >= minSelectionCount);
        JComponent component = weakRef.get();
        if (component == null) {
            dispose();
            return;
        }
        component.setVisible(newValue);

        // The following is needed to trick BoxLayout
        if (newValue) {
            component.setPreferredSize(null);
        } else {
            component.setPreferredSize(new Dimension(0, 0));
        }

        component.revalidate();
    }

    protected JComponent getComponent() {
        return weakRef.get();
    }

    public void dispose() {
        if (editor != null) {
            editor.removePropertyChangeListener(this);
            editor = null;
        }
        if (view != null) {
            view.removePropertyChangeListener(this);
            view.removeFigureSelectionListener(this);
            view = null;
        }
    }

    public void setMinSelectionCount(int newValue) {
        minSelectionCount = newValue;
        updateVisibility();
    }

    public void setVisibleIfCreationTool(boolean newValue) {
        isVisibleIfCreationTool = newValue;
    }
}

