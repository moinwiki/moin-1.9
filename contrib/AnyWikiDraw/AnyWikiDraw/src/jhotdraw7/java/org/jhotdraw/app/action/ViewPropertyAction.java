/*
 * @(#)ViewPropertyAction.java
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
 * ViewPropertyAction.
 * 
 * @author Werner Randelshofer.
 * @version $Id: ViewPropertyAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ViewPropertyAction extends AbstractViewAction {
    private String propertyName;
    private Class[] parameterClass;
    private Object propertyValue;
    private String setterName;
    private String getterName;
    
    private PropertyChangeListener viewListener = new PropertyChangeListener() {
        public void propertyChange(PropertyChangeEvent evt) {
            if (evt.getPropertyName() == propertyName) { // Strings get interned
                updateSelectedState();
            }
        }
    };
    
    /** Creates a new instance. */
    public ViewPropertyAction(Application app, String propertyName, Object propertyValue) {
        this(app, propertyName, propertyValue.getClass(), propertyValue);
    }
    public ViewPropertyAction(Application app, String propertyName, Class propertyClass, Object propertyValue) {
        super(app);
        this.propertyName = propertyName;
        this.parameterClass = new Class[] { propertyClass };
        this.propertyValue = propertyValue;
        setterName = "set"+Character.toUpperCase(propertyName.charAt(0)) +
                propertyName.substring(1);
        getterName = ((propertyClass == Boolean.TYPE || propertyClass == Boolean.class) ? "is" : "get")+
                Character.toUpperCase(propertyName.charAt(0)) +
                propertyName.substring(1);
        updateSelectedState();
    }
    
    public void actionPerformed(ActionEvent evt) {
        View p = getActiveView();
        try {
            p.getClass().getMethod(setterName, parameterClass).invoke(p, new Object[] {propertyValue});
        } catch (Throwable e) {
                InternalError error = new InternalError("Method invocation failed. setter:"+setterName+" object:"+p);
            error.initCause(e);
            throw error;
        }
    }
    
   @Override protected void installViewListeners(View p) {
        super.installViewListeners(p);
        p.addPropertyChangeListener(viewListener);
        updateSelectedState();
    }
    /**
     * Installs listeners on the view object.
     */
   @Override protected void uninstallViewListeners(View p) {
        super.uninstallViewListeners(p);
        p.removePropertyChangeListener(viewListener);
    }
    
    private void updateSelectedState() {
        boolean isSelected = false;
        View p = getActiveView();
        if (p != null) {
            try {
                Object value = p.getClass().getMethod(getterName, (Class[]) null).invoke(p);
                isSelected = value == propertyValue ||
                        value != null && propertyValue != null &&
                        value.equals(propertyValue);
            } catch (Throwable e) {
                InternalError error = new InternalError("Method invocation failed. getter:"+getterName+" object:"+p);
                error.initCause(e);
                throw error;
            }
        }
        putValue(Actions.SELECTED_KEY, isSelected);
    }
}
