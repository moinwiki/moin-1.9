/*
 * @(#)TransformEdit.java
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


package org.jhotdraw.draw;

import org.jhotdraw.util.*;
import javax.swing.undo.*;
import java.awt.geom.*;
import java.util.*;

/**
 * An {@code UndoableEdit} event which can undo a lossless transform of
 * {@link Figure}s by applying the inverse of the transform to the figures.
 * <p>
 * This object is useful for undoing lossless transformations, such as the
 * translation of figures.
 * <p>
 * If a lossy transforms is performed, such as rotation, scaling or shearing,
 * then undos should be performed with {@link TransformRestoreEdit} instead.
 *
 *
 * @author Werner Randelshofer
 * @version $Id: TransformEdit.java 536 2009-06-14 12:10:57Z rawcoder $
 */
public class TransformEdit extends AbstractUndoableEdit {
    private Collection<Figure> figures;
    private AffineTransform tx;
    
    /** Creates a new instance. */
    public TransformEdit(Figure figure, AffineTransform tx) {
        figures = new LinkedList<Figure>();
        ((LinkedList<Figure>) figures).add(figure);
        this.tx = (AffineTransform) tx.clone();
    }
    public TransformEdit(Collection<Figure> figures, AffineTransform tx) {
        this.figures = figures;
        this.tx = (AffineTransform) tx.clone();
    }
    public String getPresentationName() {
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
        return labels.getString("edit.transform.text");
    }
    
    public boolean addEdit(UndoableEdit anEdit) {
        if (anEdit instanceof TransformEdit) {
            TransformEdit that = (TransformEdit) anEdit;
            if (that.figures == this.figures) {
                this.tx.concatenate(that.tx);
                that.die();
                return true;
            }
        }
        return false;
    }
    public boolean replaceEdit(UndoableEdit anEdit) {
        if (anEdit instanceof TransformEdit) {
            TransformEdit that = (TransformEdit) anEdit;
            if (that.figures == this.figures) {
                this.tx.preConcatenate(that.tx);
                that.die();
                return true;
            }
        }
        return false;
    }
    
    public void redo() throws CannotRedoException {
        super.redo();
        for (Figure f : figures) {
            f.willChange();
            f.transform(tx);
                f.changed();
            
        }
    }
    public void undo() throws CannotUndoException {
        super.undo();
        try {
            AffineTransform inverse = tx.createInverse();
            for (Figure f : figures) {
                f.willChange();
                f.transform(inverse);
                f.changed();
            }
        } catch (NoninvertibleTransformException e) {
            e.printStackTrace();
        }
    }
    public String toString() {
        return getClass().getName()+'@'+hashCode()+" tx:"+tx;
    }
}
