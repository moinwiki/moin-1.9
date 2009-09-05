/*
 * @(#)LabelFigure.java
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

import java.awt.geom.*;
import java.util.*;

/**
 * A LabelFigure can be used to provide more double clickable area for a
 * TextHolderFigure.
 *
 * FIXME - Move FigureListener into inner class.
 *
 * @author  Werner Randelshofer
 * @version $Id: LabelFigure.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class LabelFigure extends TextFigure implements FigureListener {
    private TextHolderFigure target;
    
    /** Creates a new instance. */
    public LabelFigure() {
        this("Label");
    }
    public LabelFigure(String text) {
        setText(text);
        setEditable(false);
    }
    
    public void setLabelFor(TextHolderFigure target) {
        if (this.target != null) {
            this.target.removeFigureListener(this);
        }
        this.target = target;
        if (this.target != null) {
            this.target.addFigureListener(this);
        }
    }
    public TextHolderFigure getLabelFor() {
        return (target == null) ? this : target;
    }
    
    /**
     * Returns a specialized tool for the given coordinate.
     * <p>Returns null, if no specialized tool is available.
     */
    public Tool getTool(Point2D.Double p) {
        return (target != null && contains(p)) ? new TextEditingTool(target) : null;
    }
    
    
    public void areaInvalidated(FigureEvent e) {
    }
    
    public void attributeChanged(FigureEvent e) {
    }
    
    public void figureAdded(FigureEvent e) {
    }
    
    public void figureChanged(FigureEvent e) {
    }
    
    public void figureRemoved(FigureEvent e) {
        if (e.getFigure() == target) {
            target.removeFigureListener(this);
            target = null;
        }
    }
    
    public void figureRequestRemove(FigureEvent e) {
    }
    
    @Override
    public void remap(Map<Figure,Figure> oldToNew, boolean disconnectIfNotInMap) {
        super.remap(oldToNew, disconnectIfNotInMap);
        if (target != null) {
            Figure newTarget = (Figure) oldToNew.get(target);
            if (newTarget != null) {
                target.removeFigureListener(this);
                target = (TextHolderFigure) newTarget;
                newTarget.addFigureListener(this);
            }
        }
    }

    public void figureHandlesChanged(FigureEvent e) {
    }
}
