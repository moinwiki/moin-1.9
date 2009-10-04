/*
 * @(#)CompositeFigureEdit.java
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
package org.jhotdraw.draw;

import javax.swing.undo.CannotRedoException;
import javax.swing.undo.CannotUndoException;
import org.jhotdraw.undo.CompositeEdit;

/**
 * A {@link CompositeEdit} which invokes {@code figure.willChange}
 * and {@code figure.changed} when undoing or redoing a change.
 *
 * @author Werner Randelshofer
 * @version 1.0 2009-06-13 Created.
 */
public class CompositeFigureEdit extends CompositeEdit {

    private Figure figure;

    /**
     * Creates a new {@code CompositeFigureEdit} which uses
     * CompoundEdit.getPresentatioName and is significant.
     *
     * @see javax.swing.undo.CompoundEdit#getPresentationName()
     */
    public CompositeFigureEdit(Figure figure) {
        this.figure = figure;
    }

    /**
     * Creates new CompositeFigureEdit which uses the specified significance.
     *
     * @see javax.swing.undo.CompoundEdit#getPresentationName()
     */
    public CompositeFigureEdit(Figure figure, boolean isSignificant) {
        super(isSignificant);
        this.figure = figure;
    }

    /**
     * Creates new CompositeFigureEdit which uses the specified presentation name.
     *
     * @see javax.swing.undo.CompoundEdit#getPresentationName()
     */
    public CompositeFigureEdit(Figure figure, String presentationName) {
        super(presentationName);
        this.figure = figure;
    }

    /**
     * Creates new CompositeEdit.
     * Which uses the given presentation name.
     * If the presentation name is null, then CompoundEdit.getPresentatioName
     * is used.
     * @see javax.swing.undo.CompoundEdit#getPresentationName()
     */
    public CompositeFigureEdit(Figure figure, String presentationName, boolean isSignificant) {
        super(presentationName, isSignificant);
        this.figure = figure;
    }

    @Override
    public void undo() {
        if (!canUndo()) {
            throw new CannotUndoException();
        }
        figure.willChange();
        super.undo();
        figure.changed();
    }
    @Override
    public void redo() {
        if (!canRedo()) {
            throw new CannotRedoException();
        }
        figure.willChange();
        super.redo();
        figure.changed();
    }
}
