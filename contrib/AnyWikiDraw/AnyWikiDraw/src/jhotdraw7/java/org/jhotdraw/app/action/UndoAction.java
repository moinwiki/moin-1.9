/*
 * @(#)UndoAction.java
 *
 * Copyright (c) 1996-2007 by the original authors of JHotDraw
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
import org.jhotdraw.util.*;
import org.jhotdraw.app.Application;
import org.jhotdraw.app.View;

/**
 * Undoes the last user action.
 * In order to work, this action requires that the View returns a view-specific 
 * undo action when invoking getAction(UndoAction.ID) on the View.
 *
 * @author Werner Randelshofer
 * @version $Id: UndoAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class UndoAction extends AbstractViewAction {
    public final static String ID = "edit.undo";
    private ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
    
    private PropertyChangeListener redoActionPropertyListener = new PropertyChangeListener() {
        public void propertyChange(PropertyChangeEvent evt) {
            String name = evt.getPropertyName();
            if (name == AbstractAction.NAME) {
                putValue(AbstractAction.NAME, evt.getNewValue());
            } else if (name == "enabled") {
                updateEnabledState();
            }
        }
    };
    
    /** Creates a new instance. */
    public UndoAction(Application app) {
        super(app);
        labels.configureAction(this, ID);
    }
    
    protected void updateEnabledState() {
        boolean isEnabled = false;
        Action realRedoAction = getRealRedoAction();
        if (realRedoAction != null) {
            isEnabled = realRedoAction.isEnabled();
        }
        setEnabled(isEnabled);
    }
    
    @Override protected void updateView(View oldValue, View newValue) {
        super.updateView(oldValue, newValue);
        if (newValue != null && newValue.getAction(ID) != null) {
            putValue(AbstractAction.NAME, newValue.getAction(ID).
                    getValue(AbstractAction.NAME));
            updateEnabledState();
        }
    }
    /**
     * Installs listeners on the view object.
     */
    @Override protected void installViewListeners(View p) {
        super.installViewListeners(p);
        if (p.getAction(ID) != null) {
        p.getAction(ID).addPropertyChangeListener(redoActionPropertyListener);
        }
    }
    /**
     * Installs listeners on the view object.
     */
    @Override protected void uninstallViewListeners(View p) {
        super.uninstallViewListeners(p);
        if (p.getAction(ID) != null) {
        p.getAction(ID).removePropertyChangeListener(redoActionPropertyListener);
        }
    }
    
    public void actionPerformed(ActionEvent e) {
        Action realRedoAction = getRealRedoAction();
        if (realRedoAction != null) {
            realRedoAction.actionPerformed(e);
        }
    }
    
    private Action getRealRedoAction() {
        return (getActiveView() == null) ? null : getActiveView().getAction(ID);
    }
    
}
