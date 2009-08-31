/*
 * @(#)MoveConstrainedAction.java
 *
 * Copyright (c) 1996-2008 by the original authors of JHotDraw
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

import org.jhotdraw.draw.*;
import org.jhotdraw.undo.CompositeEdit;
import java.awt.geom.*;

/**
 * Moves the selected figures by one constrained unit.
 *
 * @author  Werner Randelshofer
 * @version $Id: MoveConstrainedAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public abstract class MoveConstrainedAction extends AbstractSelectedAction {

    private TranslationDirection dir;

    /** Creates a new instance. */
    public MoveConstrainedAction(DrawingEditor editor, TranslationDirection dir) {
        super(editor);
        this.dir = dir;
    }

    public void actionPerformed(java.awt.event.ActionEvent e) {
        if (getView().getSelectionCount() > 0) {
        
        Rectangle2D.Double r = null;
        for (Figure f : getView().getSelectedFigures()) {
            if (r == null) {
                r = f.getBounds();
            } else {
                r.add(f.getBounds());
            }
        }

        Point2D.Double p0 = new Point2D.Double(r.x, r.y);
        if (getView().getConstrainer() != null) {
            getView().getConstrainer().translateRectangle(r, dir);
        } else {
            switch (dir) {
                case NORTH:
                    r.y -= 1;
                    break;
                case SOUTH:
                    r.y += 1;
                    break;
                case WEST:
                    r.x -= 1;
                    break;
                case EAST:
                    r.x += 1;
                    break;
            }
        }

        AffineTransform tx = new AffineTransform();
        tx.translate(r.x - p0.x, r.y - p0.y);
        for (Figure f : getView().getSelectedFigures()) {
            if (f.isTransformable()) {
                f.willChange();
                f.transform(tx);
                f.changed();
            }
        }
        CompositeEdit edit;
        fireUndoableEditHappened(new TransformEdit(getView().getSelectedFigures(), tx));
        }
    }

    public static class East extends MoveConstrainedAction {

        public final static String ID = "edit.moveConstrainedEast";

        public East(DrawingEditor editor) {
            super(editor, TranslationDirection.EAST);
            labels.configureAction(this, ID);
        }
    }

    public static class West extends MoveConstrainedAction {

        public final static String ID = "edit.moveConstrainedWest";

        public West(DrawingEditor editor) {
            super(editor, TranslationDirection.WEST);
            labels.configureAction(this, ID);
        }
    }

    public static class North extends MoveConstrainedAction {

        public final static String ID = "edit.moveConstrainedNorth";

        public North(DrawingEditor editor) {
            super(editor, TranslationDirection.NORTH);
            labels.configureAction(this, ID);
        }
    }

    public static class South extends MoveConstrainedAction {

        public final static String ID = "edit.moveConstrainedSouth";

        public South(DrawingEditor editor) {
            super(editor, TranslationDirection.SOUTH);
            labels.configureAction(this, ID);
        }
    }
}
