/*
 * @(#)DefaultDrawingEditor.java
 *
 * Copyright (c) 1996-2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.draw;

import org.jhotdraw.beans.*;
import java.awt.*;
import java.awt.event.FocusEvent;
import java.awt.event.FocusListener;
import java.util.*;
import javax.swing.JComponent;
import static org.jhotdraw.draw.AttributeKeys.*;

/**
 * A default implementation of {@link DrawingEditor}.
 *
 * XXX - DefaultDrawingEditor should not publicly implement ToolListener.
 *
 * @author Werner Randelshofer
 * @version $Id: DefaultDrawingEditor.java 536 2009-06-14 12:10:57Z rawcoder $
 */
public class DefaultDrawingEditor extends AbstractBean implements DrawingEditor, ToolListener {

    private HashMap<AttributeKey, Object> defaultAttributes = new HashMap<AttributeKey, Object>();
    private HashMap<AttributeKey, Object> handleAttributes = new HashMap<AttributeKey, Object>();
    private Tool tool;
    private HashSet<DrawingView> views;
    private DrawingView activeView;
    private boolean isEnabled = true;
    private FocusListener focusHandler = new FocusListener() {

        public void focusGained(FocusEvent e) {
            setActiveView((DrawingView) findView((Container) e.getSource()));
        }

        public void focusLost(FocusEvent e) {
        /*
        if (! e.isTemporary()) {
        setFocusedView(null);
        }*/
        }
    };

    /** Creates a new instance. */
    public DefaultDrawingEditor() {
        setDefaultAttribute(FILL_COLOR, Color.white);
        setDefaultAttribute(STROKE_COLOR, Color.black);
        setDefaultAttribute(TEXT_COLOR, Color.black);

        views = new HashSet<DrawingView>();
    }

    public void setTool(Tool newValue) {
        Tool oldValue = tool;
        
        if (newValue == tool) {
            return;
        }
        if (tool != null) {
            for (DrawingView v : views) {
                v.removeMouseListener(tool);
                v.removeMouseMotionListener(tool);
                v.removeKeyListener(tool);
            }
            tool.deactivate(this);
            tool.removeToolListener(this);
        }
        tool = newValue;
        if (tool != null) {
            tool.activate(this);
            for (DrawingView v : views) {
                v.addMouseListener(tool);
                v.addMouseMotionListener(tool);
                v.addKeyListener(tool);
            }
            tool.addToolListener(this);
        }
        
        firePropertyChange(TOOL_PROPERTY, oldValue, newValue);
    }

    public void areaInvalidated(ToolEvent evt) {
        Rectangle r = evt.getInvalidatedArea();
        evt.getView().getComponent().repaint(r.x, r.y, r.width, r.height);
    }
    private Dimension preferredViewSize;

    public void toolStarted(ToolEvent evt) {
        setActiveView(evt.getView());
    }

    public void setActiveView(DrawingView newValue) {
        DrawingView oldValue = activeView;
        activeView = newValue;

        if (newValue != null && newValue != oldValue) {
            preferredViewSize = activeView.getComponent().getPreferredSize();
        }
        firePropertyChange(ACTIVE_VIEW_PROPERTY, oldValue, newValue);
    }

    public void toolDone(ToolEvent evt) {
        // XXX - Maybe we should do this with all views of the editor??
        DrawingView v = getActiveView();
        if (v != null) {
            JComponent c = v.getComponent();
            Dimension oldPreferredViewSize = preferredViewSize;
            preferredViewSize = c.getPreferredSize();
            if (oldPreferredViewSize == null || !oldPreferredViewSize.equals(preferredViewSize)) {
                c.revalidate();
            }
        }
    }

    public Tool getTool() {
        return tool;
    }

    public DrawingView getActiveView() {
        return activeView;
    }

    private void updateActiveView() {
        DrawingView aView=null;
        for (DrawingView v : views) {
            if (v.getComponent().isFocusOwner()) {
                setActiveView(v);
                return;
            }
            aView = v;
        }
        setActiveView(aView);
    }

    @SuppressWarnings("unchecked")
    public void applyDefaultAttributesTo(Figure f) {
        for (Map.Entry<AttributeKey, Object> entry : defaultAttributes.entrySet()) {
            entry.getKey().basicSet(f, entry.getValue());
        }
    }

    public <T> T getDefaultAttribute(AttributeKey<T> key) {
        if (defaultAttributes.containsKey(key)) {
            return key.get(defaultAttributes);
        } else {
            return key.getDefaultValue();
        }
    }

    public void setDefaultAttribute(AttributeKey key, Object newValue) {
        Object oldValue = defaultAttributes.put(key, newValue);
        firePropertyChange(key.getKey(), oldValue, newValue);
    }

    public void remove(DrawingView view) {
        view.getComponent().removeFocusListener(focusHandler);
        views.remove(view);
        if (tool != null) {
            view.removeMouseListener(tool);
            view.removeMouseMotionListener(tool);
            view.removeKeyListener(tool);
        }

        view.removeNotify(this);
        if (activeView == view) {
            view = (views.size() > 0) ? views.iterator().next() : null;
        }
        updateActiveView();
    }

    public void add(DrawingView view) {
        views.add(view);
        view.addNotify(this);
        view.getComponent().addFocusListener(focusHandler);
        if (tool != null) {
            view.addMouseListener(tool);
            view.addMouseMotionListener(tool);
            view.addKeyListener(tool);
        }
        updateActiveView();
    }

    public void setCursor(Cursor c) {
    }

    public Collection<DrawingView> getDrawingViews() {
        return Collections.unmodifiableCollection(views);
    }

    public DrawingView findView(Container c) {
        for (DrawingView v : views) {
            if (v.getComponent() == c) {
                return v;
            }
        }
        return null;
    }

    public void setEnabled(boolean newValue) {
        if (newValue != isEnabled) {
            boolean oldValue = isEnabled;
            isEnabled = newValue;
            firePropertyChange("enabled", oldValue, newValue);
        }
    }

    public boolean isEnabled() {
        return isEnabled;
    }

    public Map<AttributeKey, Object> getDefaultAttributes() {
        return Collections.unmodifiableMap(defaultAttributes);
    }

    public void setHandleAttribute(AttributeKey key, Object value) {
        handleAttributes.put(key, value);
    }

    public <T> T getHandleAttribute(AttributeKey<T> key) {
        if (handleAttributes.containsKey(key)) {
        return key.get(handleAttributes);
        } else {
            return key.getDefaultValue();
        }
    }
}
