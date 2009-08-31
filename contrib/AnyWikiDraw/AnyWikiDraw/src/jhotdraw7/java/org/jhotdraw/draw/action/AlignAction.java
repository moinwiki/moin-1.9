/*
 * @(#)AlignAction.java
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

import org.jhotdraw.draw.DrawingEditor;
import org.jhotdraw.draw.Figure;
import org.jhotdraw.draw.TransformEdit;
import org.jhotdraw.undo.CompositeEdit;
import java.awt.geom.*;
import java.util.*;
import org.jhotdraw.util.ResourceBundleUtil;

/**
 * Aligns the selected figures.
 *
 * XXX - Fire edit events
 *
 * @author  Werner Randelshofer
 * @version $Id: AlignAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public abstract class AlignAction extends AbstractSelectedAction {
    
    /** Creates a new instance. */
    public AlignAction(DrawingEditor editor) {
        super(editor);
    }
    public void updateEnabledState() {
        if (getView() != null) {
            setEnabled(getView().isEnabled() &&
                    getView().getSelectionCount() > 1
                    );
        } else {
            setEnabled(false);
        }
    }
    public void actionPerformed(java.awt.event.ActionEvent e) {
        CompositeEdit edit = new CompositeEdit(labels.getString("edit.align.text"));
        fireUndoableEditHappened(edit);
        alignFigures(getView().getSelectedFigures(), getSelectionBounds());
        fireUndoableEditHappened(edit);
    }
    protected abstract void alignFigures(Collection selectedFigures, Rectangle2D.Double selectionBounds);
    
    /**
     * Returns the bounds of the selected figures.
     */
    protected Rectangle2D.Double getSelectionBounds() {
        Rectangle2D.Double bounds = null;
        for (Iterator i=getView().getSelectedFigures().iterator(); i.hasNext(); ) {
            Figure f = (Figure) i.next();
            if (bounds == null) {
                bounds = f.getBounds();
            } else {
                bounds.add(f.getBounds());
            }
        }
        return bounds;
    }
    
    public static class North extends AlignAction {
        public North(DrawingEditor editor) {
            super(editor);
            labels.configureAction(this, "edit.alignNorth");
        }
        public North(DrawingEditor editor, ResourceBundleUtil labels) {
            super(editor);
            labels.configureAction(this, "edit.alignNorth");
        }
        
        protected void alignFigures(Collection selectedFigures, Rectangle2D.Double selectionBounds) {
            double y = selectionBounds.y;
            for (Iterator i=getView().getSelectedFigures().iterator(); i.hasNext(); ) {
                Figure f = (Figure) i.next();
                if (f.isTransformable()) {
                f.willChange();
                Rectangle2D.Double b = f.getBounds();
                AffineTransform tx = new AffineTransform();
                tx.translate(0, y - b.y);
                f.transform(tx);
                 f.changed();
                fireUndoableEditHappened(new TransformEdit(f, tx));
                }
           }
        }
    }
    public static class East extends AlignAction {
        public East(DrawingEditor editor) {
            super(editor);
            labels.configureAction(this, "edit.alignEast");
        }
        public East(DrawingEditor editor, ResourceBundleUtil labels) {
            super(editor);
            labels.configureAction(this, "edit.alignEast");
        }
        
        protected void alignFigures(Collection selectedFigures, Rectangle2D.Double selectionBounds) {
            double x = selectionBounds.x + selectionBounds.width;
            for (Iterator i=getView().getSelectedFigures().iterator(); i.hasNext(); ) {
                Figure f = (Figure) i.next();
                if (f.isTransformable()) {
                f.willChange();
                Rectangle2D.Double b = f.getBounds();
                AffineTransform tx = new AffineTransform();
                tx.translate(x - b.x - b.width, 0);
                f.transform(tx);
                 f.changed();
                fireUndoableEditHappened(new TransformEdit(f, tx));
                }
           }
        }
    }
    public static class West extends AlignAction {
        public West(DrawingEditor editor) {
            super(editor);
            labels.configureAction(this, "edit.alignWest");
        }
        public West(DrawingEditor editor, ResourceBundleUtil labels) {
            super(editor);
            labels.configureAction(this, "edit.alignWest");
        }
        
        protected void alignFigures(Collection selectedFigures, Rectangle2D.Double selectionBounds) {
            double x = selectionBounds.x;
            for (Iterator i=getView().getSelectedFigures().iterator(); i.hasNext(); ) {
                Figure f = (Figure) i.next();
                if (f.isTransformable()) {
                f.willChange();
                Rectangle2D.Double b = f.getBounds();
                AffineTransform tx = new AffineTransform();
                tx.translate(x - b.x, 0);
                f.transform(tx);
                f.changed();
                fireUndoableEditHappened(new TransformEdit(f, tx));
                }
            }
        }
    }
    public static class South extends AlignAction {
        public South(DrawingEditor editor) {
            super(editor);
            labels.configureAction(this, "edit.alignSouth");
        }
        public South(DrawingEditor editor, ResourceBundleUtil labels) {
            super(editor);
            labels.configureAction(this, "edit.alignSouth");
        }
        
        protected void alignFigures(Collection selectedFigures, Rectangle2D.Double selectionBounds) {
            double y = selectionBounds.y + selectionBounds.height;
            for (Iterator i=getView().getSelectedFigures().iterator(); i.hasNext(); ) {
                Figure f = (Figure) i.next();
                if (f.isTransformable()) {
                f.willChange();
                Rectangle2D.Double b = f.getBounds();
                AffineTransform tx = new AffineTransform();
                tx.translate(0, y - b.y - b.height);
                f.transform(tx);
                f.changed();
                fireUndoableEditHappened(new TransformEdit(f, tx));
                }
            }
        }
    }
    public static class Vertical extends AlignAction {
        public Vertical(DrawingEditor editor) {
            super(editor);
            labels.configureAction(this, "edit.alignVertical");
        }
        public Vertical(DrawingEditor editor, ResourceBundleUtil labels) {
            super(editor);
            labels.configureAction(this, "edit.alignVertical");
        }
        
        protected void alignFigures(Collection selectedFigures, Rectangle2D.Double selectionBounds) {
            double y = selectionBounds.y + selectionBounds.height / 2;
            for (Iterator i=getView().getSelectedFigures().iterator(); i.hasNext(); ) {
                Figure f = (Figure) i.next();
                if (f.isTransformable()) {
                f.willChange();
                Rectangle2D.Double b = f.getBounds();
                AffineTransform tx = new AffineTransform();
                tx.translate(0, y - b.y - b.height / 2);
                f.transform(tx);
                f.changed();
                fireUndoableEditHappened(new TransformEdit(f, tx));
                }
            }
        }
    }
    public static class Horizontal extends AlignAction {
        public Horizontal(DrawingEditor editor) {
            super(editor);
            labels.configureAction(this, "edit.alignHorizontal");
        }
        public Horizontal(DrawingEditor editor, ResourceBundleUtil labels) {
            super(editor);
            labels.configureAction(this, "edit.alignHorizontal");
        }
        
        protected void alignFigures(Collection selectedFigures, Rectangle2D.Double selectionBounds) {
            double x = selectionBounds.x + selectionBounds.width / 2;
            for (Iterator i=getView().getSelectedFigures().iterator(); i.hasNext(); ) {
                Figure f = (Figure) i.next();
                if (f.isTransformable()) {
                f.willChange();
                Rectangle2D.Double b = f.getBounds();
                AffineTransform tx = new AffineTransform();
                tx.translate(x - b.x - b.width / 2, 0);
                f.transform(tx);
                f.changed();
                fireUndoableEditHappened(new TransformEdit(f, tx));
                }
            }
        }
    }
}