/*
 * @(#)AbstractViewAction.java
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

import java.beans.*;
import javax.swing.*;
import org.jhotdraw.app.Application;
import org.jhotdraw.app.View;

/**
 * This abstract class can be extended to implement an {@code Action} that acts
 * on behalf of a {@link View}.
 * <p>
 * If the current View object is disabled or is null, the
 * AbstractViewAction is disabled as well.
 * <p>
 * A property name can be specified. When the specified property 
 * changes or when the current view changes, method updateView
 * is invoked.
 * 
 * @author Werner Randelshofer
 * @version $Id: AbstractViewAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public abstract class AbstractViewAction extends AbstractAction {
    private Application app;
    private String propertyName;
    public final static String VIEW_PROPERTY = "view";
    public final static String ENABLED_PROPERTY = "enabled";
    
    private PropertyChangeListener applicationListener = new PropertyChangeListener() {
        public void propertyChange(PropertyChangeEvent evt) {
            if (evt.getPropertyName() == Application.ACTIVE_VIEW_PROPERTY) { // Strings get interned
                updateView((View) evt.getOldValue(), (View) evt.getNewValue());
            }
        }
    };
    private PropertyChangeListener viewListener = new PropertyChangeListener() {
        public void propertyChange(PropertyChangeEvent evt) {
            String name = evt.getPropertyName();
            if (name == "enabled") { // Strings get interned
                updateEnabled((Boolean) evt.getOldValue(), (Boolean) evt.getNewValue());
            } else if (name == propertyName) {
                updateView();
            }
        }
    };
    
    /** Creates a new instance. */
    public AbstractViewAction(Application app) {
        this.app = app;
        this.enabled = true;
        if (app != null) {
            app.addPropertyChangeListener(applicationListener);
            updateView(null, app.getActiveView());
        }
    }
    
    /**
     * Updates the listeners of this action depending on the current view
     * of the application.
     */
    protected void updateView(View oldValue, View newValue) {
        if (oldValue != null) {
            uninstallViewListeners(oldValue);
        }
        if (newValue != null) {
            installViewListeners(newValue);
        }
        firePropertyChange(VIEW_PROPERTY, oldValue, newValue);
        updateEnabled(oldValue != null && oldValue.isEnabled(),
                newValue != null && newValue.isEnabled());
        updateView();
    }
    
    /**
     * Sets the property name.
     */
    protected void setPropertyName(String name) {
        this.propertyName = name;
        if (name != null) {
            updateView();
        }
    }
    /**
     * Gets the property name.
     */
    protected String getPropertyName() {
        return propertyName;
    }
    
    /**
     * This method is invoked, when the property changed and when
     * the view changed.
     */
    protected void updateView() {
        
    }
    
    /**
     * Installs listeners on the view object.
     */
    protected void installViewListeners(View p) {
        p.addPropertyChangeListener(viewListener);
    }
    /**
     * Uninstalls listeners on the view object.
     */
    protected void uninstallViewListeners(View p) {
        p.removePropertyChangeListener(viewListener);
    }
    
    /**
     * Updates the enabled state of this action depending on the new enabled
     * state of the view.
     */
    protected void updateEnabled(boolean oldValue, boolean newValue) {
       // System.out.println("AbstractViewAction updateEnabled"+oldValue+","+newValue);
        firePropertyChange("enabled", oldValue, newValue && isEnabled());
    }
    
    public Application getApplication() {
        return app;
    }
    public View getActiveView() {
        return app.getActiveView();
    }
    
    /**
     * Returns true if the action is enabled.
     * The enabled state of the action depends on the state that has been set
     * using setEnabled() and on the enabled state of the application.
     *
     * @return true if the action is enabled, false otherwise
     * @see Action#isEnabled
     */
    @Override public boolean isEnabled() {
        return getActiveView() != null && 
                getActiveView().isEnabled() &&
                this.enabled;
    }
    
    /**
     * Enables or disables the action. The enabled state of the action
     * depends on the value that is set here and on the enabled state of
     * the application.
     *
     * @param newValue  true to enable the action, false to
     *                  disable it
     * @see Action#setEnabled
     */
    @Override public void setEnabled(boolean newValue) {
        boolean oldValue = this.enabled;
        this.enabled = newValue;
        
        boolean projIsEnabled = getActiveView() != null && getActiveView().isEnabled();
        
        firePropertyChange(ENABLED_PROPERTY,
                Boolean.valueOf(oldValue && projIsEnabled),
                Boolean.valueOf(newValue && projIsEnabled)
                );
        
    }
}
