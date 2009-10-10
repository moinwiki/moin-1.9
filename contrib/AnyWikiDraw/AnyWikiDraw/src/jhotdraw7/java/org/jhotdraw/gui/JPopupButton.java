/*
 * @(#)JPopupButton.java
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
package org.jhotdraw.gui;

import org.jhotdraw.gui.plaf.palette.PaletteMenuItemUI;
import java.awt.*;
import java.beans.*;
import javax.swing.*;
import java.awt.event.*;
import org.jhotdraw.draw.action.*;

/**
 * JPopupButton provides a popup menu.
 *
 * @author  Werner Randelshofer
 * @version $Id: JPopupButton.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class JPopupButton extends javax.swing.JButton {

    private JPopupMenu popupMenu;
    private int columnCount = 1;
    private Action action;
    private Rectangle actionArea;
    private Font itemFont;
    public final static Font ITEM_FONT = new Font("Dialog", Font.PLAIN, 10);
    private int popupAnchor = SwingConstants.SOUTH_WEST;

    private class ActionPropertyHandler implements PropertyChangeListener {

        public void propertyChange(PropertyChangeEvent evt) {
            if (evt.getPropertyName().equals("enabled")) {
                setEnabled(((Boolean) evt.getNewValue()).booleanValue());
            } else {
                repaint();
            }
        }
    };
    private ActionPropertyHandler actionPropertyHandler = new ActionPropertyHandler();

    /** Creates new form JToolBarMenu */
    public JPopupButton() {
        initComponents();
        setFocusable(false);
        itemFont = ITEM_FONT;
    }

    public void setItemFont(Font newValue) {
        itemFont = newValue;
        if (popupMenu != null) {
            updateFont(popupMenu);
        }
    }

    public void setAction(Action action, Rectangle actionArea) {
        if (this.action != null) {
            this.action.removePropertyChangeListener(actionPropertyHandler);
        }

        this.action = action;
        this.actionArea = actionArea;

        if (action != null) {
            action.addPropertyChangeListener(actionPropertyHandler);
        }
    }

    public int getColumnCount() {
        return columnCount;
    }

    public void setColumnCount(int count, boolean isVertical) {
        columnCount = count;
        getPopupMenu().setLayout(new VerticalGridLayout(0, getColumnCount(), isVertical));
    }

    public AbstractButton add(Action action) {
        JMenuItem item = getPopupMenu().add(action);
        if (getColumnCount() > 1) {
            item.setUI(new PaletteMenuItemUI());
        }
        item.setFont(itemFont);
        return item;
    }

    public void add(JMenu submenu) {
        JMenuItem item = getPopupMenu().add(submenu);
        updateFont(submenu);
    }

    public void add(JComponent submenu) {
        getPopupMenu().add(submenu);
    }

    private void updateFont(MenuElement menu) {
        menu.getComponent().setFont(itemFont);
        for (MenuElement child : menu.getSubElements()) {
            updateFont(child);
        }
    }

    public void add(JMenuItem item) {
        getPopupMenu().add(item);
        item.setFont(itemFont);
    }

    public void addSeparator() {
        getPopupMenu().addSeparator();
    }

    public void setPopupMenu(JPopupMenu popupMenu) {
        this.popupMenu = popupMenu;
    }

    public JPopupMenu getPopupMenu() {
        if (popupMenu == null) {
            popupMenu = new JPopupMenu();
            popupMenu.setLayout(new VerticalGridLayout(0, getColumnCount()));
        }
        return popupMenu;
    }

    public void setPopupAlpha(float newValue) {
        float oldValue = getPopupAlpha();
        getPopupMenu().putClientProperty("Quaqua.PopupMenu.alpha", newValue);
        firePropertyChange("popupAlpha", oldValue, newValue);
    }

    public float getPopupAlpha() {
        Float value = (Float) getPopupMenu().getClientProperty("Quaqua.PopupMenu.alpha");
        return (value == null) ? 0.75f : value.floatValue();
    }

    /**
     * Gets the popup anchor.
     * 
     * @return SwingConstants.SOUTH_WEST or SOUTH_EAST.
     */
    public int getPopupAnchor() {
        return popupAnchor;
    }

    /**
     * Sets the popup anchor.
     * <p>
     * <ul>
     * <li>SOUTH_WEST places the popup below the button and aligns it with its 
     * left bound.</li>
     * <li>SOUTH_EAST places the popup below the button and aligns it with its 
     * right bound.</li>
     * </ul> 
     * 
     * @param newValue SwingConstants.SOUTH_WEST or SOUTH_EAST.
     */
    public void setPopupAnchor(int newValue) {
        popupAnchor = newValue;
    }

    protected void showPopup(java.awt.event.MouseEvent evt) {
        // Add your handling code here:
        if (popupMenu != null && (actionArea == null || !actionArea.contains(evt.getX() - getInsets().left, evt.getY() - getInsets().top))) {
            int x, y;

            switch (popupAnchor) {
                case SOUTH_EAST:
                    x = getWidth() - popupMenu.getPreferredSize().width;
                    ;
                    y = getHeight();
                    break;
                case SOUTH_WEST:
                default:
                    x = 0;
                    y = getHeight();
                    break;
            }
            if (getParent() instanceof JToolBar) {
                JToolBar toolbar = (JToolBar) getParent();
                if (toolbar.getOrientation() == JToolBar.VERTICAL) {
                    y = 0;
                    if (toolbar.getX() > toolbar.getParent().getInsets().left) {
                        x = -popupMenu.getPreferredSize().width;
                    } else {
                        x = getWidth();
                    }
                } else {
                    if (toolbar.getY() > toolbar.getParent().getInsets().top) {
                        y = -popupMenu.getPreferredSize().height;
                    }
                }
            }

            popupMenu.show(this, x, y);
            popupMenu.repaint();
        }
    }

    /** This method is called from within the constructor to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        addMouseListener(new java.awt.event.MouseAdapter() {
            public void mousePressed(java.awt.event.MouseEvent evt) {
                handleMousePressed(evt);
            }
            public void mouseReleased(java.awt.event.MouseEvent evt) {
                performAction(evt);
            }
        });
    }// </editor-fold>//GEN-END:initComponents

    private void performAction(java.awt.event.MouseEvent evt) {//GEN-FIRST:event_performAction
        // Add your handling code here:
        if (actionArea != null && actionArea.contains(evt.getX() - getInsets().left, evt.getY() - getInsets().top)) {
            action.actionPerformed(
                    new ActionEvent(this,
                    ActionEvent.ACTION_PERFORMED,
                    null,
                    evt.getWhen(),
                    evt.getModifiers()));

        }
    }//GEN-LAST:event_performAction

    private void handleMousePressed(java.awt.event.MouseEvent evt) {//GEN-FIRST:event_handleMousePressed
        showPopup(evt);

}//GEN-LAST:event_handleMousePressed
    // Variables declaration - do not modify//GEN-BEGIN:variables
    // End of variables declaration//GEN-END:variables
}
