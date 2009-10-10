/*
 * @(#)ProjectPropertyAction.java
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
import java.beans.*;
import org.jhotdraw.app.Application;
import org.jhotdraw.app.View;

/**
 * ToggleViewPropertyAction.
 *
 * @author Werner Randelshofer.
 * @version $Id: ToggleViewPropertyAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ToggleViewPropertyAction extends AbstractViewAction {
    private String propertyName;
    private Class[] parameterClass;
    private Object selectedPropertyValue;
    private Object deselectedPropertyValue;
    private String setterName;
    private String getterName;
    
    private PropertyChangeListener viewListener = new PropertyChangeListener() {
        public void propertyChange(PropertyChangeEvent evt) {
            if (evt.getPropertyName() == propertyName) { // Strings get interned
                updateView();
            }
        }
    };
    
    /** Creates a new instance. */
    public ToggleViewPropertyAction(Application app, String propertyName) {
        this(app, propertyName, Boolean.TYPE, true, false);
    }
    public ToggleViewPropertyAction(Application app, String propertyName, Class propertyClass,
            Object selectedPropertyValue, Object deselectedPropertyValue) {
        super(app);
        this.propertyName = propertyName;
        this.parameterClass = new Class[] { propertyClass };
        this.selectedPropertyValue = selectedPropertyValue;
        this.deselectedPropertyValue = deselectedPropertyValue;
        setterName = "set"+Character.toUpperCase(propertyName.charAt(0)) +
                propertyName.substring(1);
        getterName = ((propertyClass == Boolean.TYPE || propertyClass == Boolean.class) ? "is" : "get")+
                Character.toUpperCase(propertyName.charAt(0)) +
                propertyName.substring(1);
        updateView();
    }
    
    public void actionPerformed(ActionEvent evt) {
        View p = getActiveView();
        Object value = getCurrentValue();
        Object newValue = (value == selectedPropertyValue ||
                        value != null && selectedPropertyValue != null &&
                        value.equals(selectedPropertyValue)) ?
                            deselectedPropertyValue :
                            selectedPropertyValue;
        try {
            p.getClass().getMethod(setterName, parameterClass).invoke(p, new Object[] {newValue});
        } catch (Throwable e) {
                InternalError error = new InternalError("No "+setterName+" method on "+p);
            error.initCause(e);
            throw error;
        }
    }
    
    private Object getCurrentValue() {
        View p = getActiveView();
        if (p != null) {
            try {
                return p.getClass().getMethod(getterName, (Class[]) null).invoke(p);
            } catch (Throwable e) {
                InternalError error = new InternalError("No "+getterName+" method on "+p);
                error.initCause(e);
                throw error;
            }
        }
        return null;
    }
    
    
    protected void installViewListeners(View p) {
        super.installViewListeners(p);
        p.addPropertyChangeListener(viewListener);
        updateView();
    }
    /**
     * Installs listeners on the view object.
     */
    protected void uninstallViewListeners(View p) {
        super.uninstallViewListeners(p);
        p.removePropertyChangeListener(viewListener);
    }
    
    @Override protected void updateView() {
        boolean isSelected = false;
        View p = getActiveView();
        if (p != null) {
            try {
                Object value = p.getClass().getMethod(getterName, (Class[]) null).invoke(p);
                isSelected = value == selectedPropertyValue ||
                        value != null && selectedPropertyValue != null &&
                        value.equals(selectedPropertyValue);
            } catch (Throwable e) {
                InternalError error = new InternalError("No "+getterName+" method on "+p);
                error.initCause(e);
                throw error;
            }
        }
        putValue(Actions.SELECTED_KEY, isSelected);
    }
}
