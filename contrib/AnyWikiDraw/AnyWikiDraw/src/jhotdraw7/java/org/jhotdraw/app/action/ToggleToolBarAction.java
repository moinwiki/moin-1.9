/*
 * @(#)ToggleToolBarAction.java
 *
 * Copyright (c) 1996-2006 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.app.action;

import java.awt.event.*;
import javax.swing.*;
import java.beans.*;

/**
 * ToggleToolBarAction.
 * 
 * @author Werner Randelshofer
 * @version $Id: ToggleToolBarAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ToggleToolBarAction extends AbstractAction {
    private JToolBar toolBar;
    private PropertyChangeListener propertyHandler;
    
    /** Creates a new instance. */
    public ToggleToolBarAction(JToolBar toolBar, String label) {
        super(label);
        
        propertyHandler = new PropertyChangeListener() {
            public void propertyChange(PropertyChangeEvent evt) {
                String name = evt.getPropertyName();
                if (name.equals("visible")) {
                    putValue(Actions.SELECTED_KEY, evt.getNewValue());
                }
            }            
        };
        
        putValue(Actions.SELECTED_KEY, true);
        setToolBar(toolBar);
    }
    
    public void putValue(String key, Object newValue) {
        super.putValue(key, newValue);
        if (key == Actions.SELECTED_KEY) {
            if (toolBar != null) {
                toolBar.setVisible((Boolean) newValue);
            }
        }
    }
    
    public void setToolBar(JToolBar newValue) {
        if (toolBar != null) {
            toolBar.removePropertyChangeListener(propertyHandler);
        }
        
        toolBar = newValue;
 
        if (toolBar != null) {
            toolBar.addPropertyChangeListener(propertyHandler);
            putValue(Actions.SELECTED_KEY, toolBar.isVisible());
        }
    }
    
    public void actionPerformed(ActionEvent e) {
        if (toolBar != null) {
            putValue(Actions.SELECTED_KEY, ! toolBar.isVisible());
        }
    }
}
