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
import java.util.Collections;
import java.util.Map;
import java.util.Set;
import org.jhotdraw.draw.AttributeKey;
import org.jhotdraw.draw.DrawingEditor;
import org.jhotdraw.draw.Figure;

/**
 * FigureAttributeEditorHandler mediates between an AttributeEditor and the
 * currently selected Figure's in a DrawingEditor.
 *
 * @author Werner Randelshofer
 * @version $Id: FigureAttributeEditorHandler.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class FigureAttributeEditorHandler<T> extends AbstractAttributeEditorHandler<T> {

    public FigureAttributeEditorHandler(AttributeKey<T> key, AttributeEditor<T> attributeEditor, DrawingEditor drawingEditor) {
        super(key, attributeEditor, drawingEditor);
    }

    public FigureAttributeEditorHandler(AttributeKey<T> key, AttributeEditor<T> attributeEditor, DrawingEditor drawingEditor, boolean updateDrawingEditorDefaults) {
        super(key, attributeEditor, drawingEditor, updateDrawingEditorDefaults);
    }
    public FigureAttributeEditorHandler(AttributeKey<T> key, Map<AttributeKey,Object> defaultAttributes, AttributeEditor<T> attributeEditor, DrawingEditor drawingEditor, boolean updateDrawingEditorDefaults) {
        super(key, defaultAttributes, attributeEditor, drawingEditor, updateDrawingEditorDefaults);
    }

    @Override
    @SuppressWarnings("unchecked")
    protected Set<Figure> getEditedFigures() {
        return (Set<Figure>) ((activeView == null) ? Collections.emptySet() : activeView.getSelectedFigures());
    }

}
