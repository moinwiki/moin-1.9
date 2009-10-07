/**
 * @(#)ToolBarLayout.java
 *
 * Copyright (c) 2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.gui;

import java.awt.*;
import java.io.Serializable;
import javax.swing.BoxLayout;

/**
 * A layout which lays out components horizontally or vertically according
 * to their preferred size.
 *
 * @author Werner Randelshofer
 * @version $Id: ToolBarLayout.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ToolBarLayout implements LayoutManager2, Serializable {

    /**
     * Specifies that components should be laid out left to right.
     */
    public static final int X_AXIS = 0;
    /**
     * Specifies that components should be laid out top to bottom.
     */
    public static final int Y_AXIS = 1;
    /**
     * Specifies the axis of the layout.
     */
    private int axis;

    /**
     * Creates a layout manager that will lay out components along the
     * X-axis.  
     */
    public ToolBarLayout() {
        this(X_AXIS);
    }
    /**
     * Creates a layout manager that will lay out components along the
     * given axis.  
     *
     * @param axis  the axis to lay out components along. Can be one of:
     *              <code>BoxLayout.X_AXIS</code>,
     *              <code>BoxLayout.Y_AXIS</code>,
     *
     * @exception AWTError  if the value of <code>axis</code> is invalid 
     */
    public ToolBarLayout(int axis) {
        this.axis = axis;
    }


    public void addLayoutComponent(Component comp, Object constraints) {
    }

    public Dimension maximumLayoutSize(Container target) {
        return preferredLayoutSize(target);
    }

    public float getLayoutAlignmentX(Container target) {
        switch (axis) {
            case Y_AXIS:
                return 0f;
            case X_AXIS:
            default:
                return 0f;
        }
    }

    public float getLayoutAlignmentY(Container target) {
        switch (axis) {
            case Y_AXIS:
                return 0f;
            case X_AXIS:
            default:
                return 0f;
        }
    }

    public void invalidateLayout(Container target) {
    }

    public void addLayoutComponent(String name, Component comp) {
    }

    public void removeLayoutComponent(Component comp) {
    }

    public Dimension preferredLayoutSize(Container parent) {
        int w = 0;
        int h = 0;
        switch (axis) {
            case Y_AXIS:
                for (Component c : parent.getComponents()) {
                    Dimension ps = c.getPreferredSize();
                    w = Math.max(w, ps.width);
                    h += ps.height;
                }
                break;
            case X_AXIS:
            default:
                for (Component c : parent.getComponents()) {
                    Dimension ps = c.getPreferredSize();
                    h = Math.max(h, ps.height);
                    w += ps.width;
                }
        }
        
        Insets i = parent.getInsets();
        
        return new Dimension(w + i.left + i.right, h + i.top + i.bottom);
    }

    public Dimension minimumLayoutSize(Container parent) {
        return preferredLayoutSize(parent);
    }

    public void layoutContainer(Container parent) {
        Dimension ps = preferredLayoutSize(parent);
        Insets insets = parent.getInsets();
        
        int w = ps.width - insets.left - insets.right;
        int h = ps.height - insets.top - insets.bottom;
        int x = insets.left;
        int y = insets.top;
        switch (axis) {
            case Y_AXIS:
                for (Component c : parent.getComponents()) {
                    ps = c.getPreferredSize();
                    c.setBounds(x, y, w, ps.height);
                    y += ps.height;
                }
                break;
            case X_AXIS:
            default:
                for (Component c : parent.getComponents()) {
                    ps = c.getPreferredSize();
                    c.setBounds(x, y, ps.width, h);
                    x += ps.width;
                }
        }
    }
}
