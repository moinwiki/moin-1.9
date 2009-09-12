/*
 * @(#)ZoomEditorAction.java
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

package org.jhotdraw.draw.action;

import org.jhotdraw.draw.DrawingEditor;
import org.jhotdraw.draw.DrawingView;
import javax.swing.*;

/**
 * Zooms either the current view or all views of a DrawingEditor.
 *
 * @author  Werner Randelshofer
 * @version $Id: ZoomEditorAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ZoomEditorAction extends AbstractDrawingEditorAction {
    public final static String ID = "zoomEditor";
    
    private double scaleFactor;
    private AbstractButton button;
    private String label;
    private boolean updateAllViews;
    /**
     * Creates a new instance.
     */
    public ZoomEditorAction(DrawingEditor editor, double scaleFactor, AbstractButton button) {
        this(editor, scaleFactor, button, true);
        
    }
    /**
     * Creates a new instance.
     */
    public ZoomEditorAction(DrawingEditor editor, double scaleFactor, AbstractButton button, boolean updateAllViews) {
        super(editor);
        this.scaleFactor = scaleFactor;
        this.button = button;
        this.updateAllViews = updateAllViews;
        label = (int) (scaleFactor * 100)+" %";
        putValue(Action.DEFAULT, label);
        putValue(Action.NAME, label);
    }
    
    public void actionPerformed(java.awt.event.ActionEvent e) {
        if (button != null) {
            button.setText(label);
        }
        if (updateAllViews) {
        for (DrawingView v : getEditor().getDrawingViews()) {
            v.setScaleFactor(scaleFactor);
        }} else {
            getView().setScaleFactor(scaleFactor);
        }
    }
}
