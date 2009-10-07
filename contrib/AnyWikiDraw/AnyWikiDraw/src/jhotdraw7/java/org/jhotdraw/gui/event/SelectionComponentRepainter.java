/**
 * @(#)SelectionComponentRepainter.java
 *
 * Copyright (c) 2008-2009 by the original authors of JHotDraw
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

import java.beans.*;
import javax.swing.*;
import org.jhotdraw.beans.Disposable;
import org.jhotdraw.draw.*;

/**
 * Calls repaint on components, which show attributes of the drawing editor
 * and of its views based on the current selection.
 *
 * @author Werner Randelshofer
 * @version $Id: SelectionComponentRepainter.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class SelectionComponentRepainter extends FigureAdapter
        implements PropertyChangeListener, FigureSelectionListener, Disposable {

    private DrawingEditor editor;
    private JComponent component;

    public SelectionComponentRepainter(DrawingEditor editor, JComponent component) {
        this.editor = editor;
        this.component = component;
        if (editor != null) {
            if (editor.getActiveView() != null) {
                DrawingView view = editor.getActiveView();
                view.addPropertyChangeListener(this);
                view.addFigureSelectionListener(this);
                if (view.getDrawing() != null) {
                    view.getDrawing().addFigureListener(this);
                }
            }
            editor.addPropertyChangeListener(this);
        }
    }

    @Override
    public void attributeChanged(FigureEvent evt) {
        component.repaint();
    }

    public void propertyChange(PropertyChangeEvent evt) {
        String name = evt.getPropertyName();
        if (name == DrawingEditor.ACTIVE_VIEW_PROPERTY) {
            DrawingView view = (DrawingView) evt.getOldValue();
            if (view != null) {
                view.removePropertyChangeListener(this);
                view.removeFigureSelectionListener(this);
                if (view.getDrawing() != null) {
                    view.getDrawing().removeFigureListener(this);
                }
            }
            view = (DrawingView) evt.getNewValue();
            if (view != null) {
                view.addPropertyChangeListener(this);
                view.addFigureSelectionListener(this);
                if (view.getDrawing() != null) {
                    view.getDrawing().addFigureListener(this);
                }
            }
            component.repaint();
        } else if (name == DrawingView.DRAWING_PROPERTY) {
            Drawing drawing = (Drawing) evt.getOldValue();
            if (drawing != null) {
                drawing.removeFigureListener(this);
            }
            drawing = (Drawing) evt.getNewValue();
            if (drawing != null) {
                drawing.addFigureListener(this);
            }
            component.repaint();
        } else {
            component.repaint();
        }
    }

    public void selectionChanged(FigureSelectionEvent evt) {
        component.repaint();
    }

    public void dispose() {
        if (editor != null) {
            if (editor.getActiveView() != null) {
                DrawingView view = editor.getActiveView();
                view.removePropertyChangeListener(this);
                view.removeFigureSelectionListener(this);
                if (view.getDrawing() != null) {
                    view.getDrawing().removeFigureListener(this);
                }
            }
            editor.removePropertyChangeListener(this);
            editor = null;
        }
        component = null;
    }
}

