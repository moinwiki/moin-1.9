/*
 * @(#)FigureAttributeEditorHandler.java
 * 
 * Copyright (c) 2009 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 * 
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.gui.event;

import org.jhotdraw.gui.*;
import org.jhotdraw.gui.event.AbstractAttributeEditorHandler;
import java.util.HashSet;
import java.util.Set;
import org.jhotdraw.draw.AttributeKey;
import org.jhotdraw.draw.Drawing;
import org.jhotdraw.draw.DrawingEditor;
import org.jhotdraw.draw.Figure;

/**
 * FigureAttributeEditorHandler mediates between an AttributeEditor and the
 * currently selected Figure's in a DrawingEditor.
 *
 * @author Werner Randelshofer
 * @version $Id: DrawingAttributeEditorHandler.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class DrawingAttributeEditorHandler<T> extends AbstractAttributeEditorHandler<T> {

    private Drawing drawing;

    public DrawingAttributeEditorHandler(AttributeKey<T> key, AttributeEditor<T> attributeEditor, DrawingEditor drawingEditor) {
        super(key, attributeEditor, drawingEditor, false);
    }

    public void setDrawing(Drawing newValue) {
        drawing = newValue;
        updateAttributeEditor();
    }

    public Drawing getDrawing() {
        return drawing;
    }

    @Override
    protected Set<Figure> getEditedFigures() {
        HashSet<Figure> s = new HashSet<Figure>();
        if (drawing != null) {
            s.add(drawing);
        } else if (activeView != null) {
            s.add(activeView.getDrawing());
        }
        return s;
    }
}
