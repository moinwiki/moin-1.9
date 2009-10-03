/*
 * @(#)NewAction.java
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

import org.jhotdraw.util.*;
import java.awt.event.*;
import org.jhotdraw.app.Application;
import org.jhotdraw.app.View;

/**
 * Creates a new view.
 *
 * @author Werner Randelshofer
 * @version $Id: NewAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class NewAction extends AbstractApplicationAction {
    public final static String ID = "file.new";
    
    /** Creates a new instance. */
    public NewAction(Application app) {
        super(app);
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        labels.configureAction(this, ID);
    }
    
    public void actionPerformed(ActionEvent evt) {
        Application app = getApplication();
        final View newP = app.createView();
        int multiOpenId = 1;
        for (View existingP : app.views()) {
            if (existingP.getFile() == null) {
                multiOpenId = Math.max(multiOpenId, existingP.getMultipleOpenId() + 1);
            }
        }
        newP.setMultipleOpenId(multiOpenId);
        app.add(newP);
        newP.execute(new Runnable() {
            public void run() {
                newP.clear();
            }
        });
        app.show(newP);
    }
}
