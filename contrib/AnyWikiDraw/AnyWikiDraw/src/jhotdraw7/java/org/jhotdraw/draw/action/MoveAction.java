/*
 * @(#)MoveAction.java
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
import org.jhotdraw.draw.Figure;
import org.jhotdraw.draw.TransformEdit;
import org.jhotdraw.undo.CompositeEdit;
import java.awt.geom.*;

/**
 * Moves the selected figures by one unit.
 *
 * @author  Werner Randelshofer
 * @version $Id: MoveAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public abstract class MoveAction extends AbstractSelectedAction {
    private int dx, dy;
    
    /** Creates a new instance. */
    public MoveAction(DrawingEditor editor, int dx, int dy) {
        super(editor);
        this.dx = dx;
        this.dy = dy;
    }
    
    public void actionPerformed(java.awt.event.ActionEvent e) {
        CompositeEdit edit;
        AffineTransform tx = new AffineTransform();
        tx.translate(dx, dy);
        for (Figure f : getView().getSelectedFigures()) {
            f.willChange();
            f.transform(tx);
            f.changed();
        }
        fireUndoableEditHappened(new TransformEdit(getView().getSelectedFigures(), tx));
        
    }
    
    public static class East extends MoveAction {
        public final static String ID = "edit.moveEast";
        public East(DrawingEditor editor) {
            super(editor, 1, 0);
            labels.configureAction(this, ID);
        }
    }
    public static class West extends MoveAction {
        public final static String ID = "edit.moveWest";
        public West(DrawingEditor editor) {
            super(editor, -1, 0);
            labels.configureAction(this, ID);
        }
    }
    public static class North extends MoveAction {
        public final static String ID = "edit.moveNorth";
        public North(DrawingEditor editor) {
            super(editor, 0, -1);
            labels.configureAction(this, ID);
        }
    }
    public static class South extends MoveAction {
        public final static String ID = "edit.moveSouth";
        public South(DrawingEditor editor) {
            super(editor, 0, 1);
            labels.configureAction(this, ID);
        }
    }
}
