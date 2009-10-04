/*
 * @(#)ClearRecentFilesAction.java
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

import org.jhotdraw.util.*;
import java.awt.event.ActionEvent;
import java.beans.*;
import org.jhotdraw.app.Application;

/**
 * ClearRecentFilesAction.
 *
 * @author Werner Randelshofer.
 * @version $Id: ClearRecentFilesAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ClearRecentFilesAction extends AbstractApplicationAction {
    public final static String ID = "file.clearRecentFiles";
    
    private PropertyChangeListener applicationListener;
    
    /** Creates a new instance. */
    public ClearRecentFilesAction(Application app) {
        super(app);
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        labels.configureAction(this, ID);
        updateEnabled();
    }
    
    /**
     * Installs listeners on the application object.
     */
    @Override protected void installApplicationListeners(Application app) {
        super.installApplicationListeners(app);
        if (applicationListener == null) {
            applicationListener = createApplicationListener();
        }
        app.addPropertyChangeListener(applicationListener);
    }
    private PropertyChangeListener createApplicationListener() {
        return new PropertyChangeListener() {
            public void propertyChange(PropertyChangeEvent evt) {
                if (evt.getPropertyName() == "recentFiles") { // Strings get interned
                    updateEnabled();
                }
            }
        };
    }
    /**
     * Installs listeners on the application object.
     */
    @Override protected void uninstallApplicationListeners(Application app) {
        super.uninstallApplicationListeners(app);
        app.removePropertyChangeListener(applicationListener);
    }
    
    public void actionPerformed(ActionEvent e) {
        getApplication().clearRecentFiles();
    }
    
    private void updateEnabled() {
        setEnabled(getApplication().recentFiles().size() > 0);
        
    }
    
}
