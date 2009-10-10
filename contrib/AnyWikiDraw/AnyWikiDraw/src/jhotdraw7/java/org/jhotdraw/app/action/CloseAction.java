/*
 * @(#)CloseAction.java
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

import java.awt.event.*;
import javax.swing.*;
import org.jhotdraw.app.Application;
import org.jhotdraw.app.View;

/**
 * Closes a view.
 *
 * @author  Werner Randelshofer
 * @version $Id: CloseAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class CloseAction extends AbstractSaveBeforeAction {
    public final static String ID = "file.close";
    
    /** Creates a new instance. */
    public CloseAction(Application app) {
        super(app);
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        labels.configureAction(this, ID);
    }
    
    @Override protected void doIt(View view) {
        if (view != null && view.getApplication() != null) {
            view.getApplication().
                    dispose(view);
        }
    }
}
