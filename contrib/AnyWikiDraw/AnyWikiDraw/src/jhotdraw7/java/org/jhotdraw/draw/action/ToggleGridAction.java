/*
 * @(#)ToggleGridAction.java
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

package org.jhotdraw.draw.action;

import org.jhotdraw.app.action.*;
import org.jhotdraw.draw.*;
import org.jhotdraw.util.ResourceBundleUtil;

/**
 * Toggles the grid of the current view.
 *
 * @author  Werner Randelshofer
 * @version $Id: ToggleGridAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ToggleGridAction extends AbstractDrawingViewAction {
    public final static String ID = "view.toggleGrid";
    /**
     * Creates a new instance.
     */
    public ToggleGridAction(DrawingEditor editor) {
        super(editor);
        ResourceBundleUtil labels =
                ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
        labels.configureAction(this, ID);
        updateViewState();
    }
    
    public void actionPerformed(java.awt.event.ActionEvent e) {
        DrawingView view = getView();
        if (view != null) {
            view.setConstrainerVisible(! view.isConstrainerVisible());
        }
    }
    
    @Override
    protected void updateViewState() {
        DrawingView view = getView();
        putValue(Actions.SELECTED_KEY, view != null && view.isConstrainerVisible());
    }
}
