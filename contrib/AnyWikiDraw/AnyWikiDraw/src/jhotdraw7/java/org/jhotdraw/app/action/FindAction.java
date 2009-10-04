/*
 * @(#)FindAction.java
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
import org.jhotdraw.app.*;
import org.jhotdraw.util.*;

/**
 * Presents a printer dialog to the user and then prints the View to the
 * chosen printer.
 * <p>
 * This action requires that the view has the following additional methods:
 * <pre>
 * public void find();
 * </pre>
 * <p>
 * The FindAction invokes this method using Java Reflection. Thus there is
 * no Java Interface that the View needs to implement.
 *
 * @see org.jhotdraw.draw.DrawingPageable
 *
 * @author Werner Randelshofer
 * @version $Id: FindAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class FindAction extends AbstractViewAction {
    public final static String ID = "edit.find";
    
    /** Creates a new instance. */
    public FindAction(Application app) {
        super(app);
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        labels.configureAction(this, ID);
    }
    
    public void actionPerformed(ActionEvent evt) {
        View view = getActiveView();
        try {
            Methods.invoke(view, "find");
        } catch (NoSuchMethodException ex) {
            ex.printStackTrace();
        }
    }
}
