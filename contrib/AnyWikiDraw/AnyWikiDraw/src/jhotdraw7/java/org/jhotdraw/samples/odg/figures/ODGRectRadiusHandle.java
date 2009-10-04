/*
 * @(#)ODGRectRadiusHandle.java
 *
 * Copyright (c) 2007 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.samples.odg.figures;

import javax.swing.undo.*;
import org.jhotdraw.draw.*;
import org.jhotdraw.geom.*;
import org.jhotdraw.util.*;
import org.jhotdraw.undo.*;
import java.awt.*;
import java.awt.geom.*;
import static org.jhotdraw.samples.odg.ODGAttributeKeys.*;

/**
 * A Handle to manipulate the radius of a round lead rectangle.
 *
 * @author  Werner Randelshofer
 * @version $Id: ODGRectRadiusHandle.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ODGRectRadiusHandle extends AbstractHandle {
    private final static boolean DEBUG = false;
    private static final int OFFSET = 6;
    private Dimension2DDouble originalArc2D;
    CompositeEdit edit;
    
    /** Creates a new instance. */
    public ODGRectRadiusHandle(Figure owner) {
        super(owner);
    }
    
    /**
     * Draws this handle.
     */
    public void draw(Graphics2D g) {
        drawDiamond(g, Color.yellow, Color.black);
    }
    
    protected Rectangle basicGetBounds() {
        Rectangle r = new Rectangle(locate());
        r.grow(getHandlesize() / 2 + 1, getHandlesize() / 2 + 1);
        return r;
    }
    
    private Point locate() {
        ODGRectFigure owner = (ODGRectFigure) getOwner();
        Rectangle2D.Double r = owner.getBounds();
        Point2D.Double p = new Point2D.Double(
                r.x + owner.getArcWidth(),
                r.y + owner.getArcHeight()
                );
        if (TRANSFORM.get(owner) != null) {
            TRANSFORM.get(owner).transform(p, p);
        }
        return view.drawingToView(p);
    }
    
    public void trackStart(Point anchor, int modifiersEx) {
        ODGRectFigure odgRect = (ODGRectFigure) getOwner();
        originalArc2D = odgRect.getArc();
    }
    
    public void trackStep(Point anchor, Point lead, int modifiersEx) {
        int dx = lead.x - anchor.x;
        int dy = lead.y - anchor.y;
        ODGRectFigure odgRect = (ODGRectFigure) getOwner();
        odgRect.willChange();
        Point2D.Double p = view.viewToDrawing(lead);
        if (TRANSFORM.get(odgRect) != null) {
            try {
                TRANSFORM.get(odgRect).inverseTransform(p, p);
            } catch (NoninvertibleTransformException ex) {
                if (DEBUG) ex.printStackTrace();
            }
        }
        Rectangle2D.Double r = odgRect.getBounds();
        odgRect.setArc(p.x - r.x, p.y - r.y);
        odgRect.changed();
    }
    public void trackEnd(Point anchor, Point lead, int modifiersEx) {
        final ODGRectFigure odgRect = (ODGRectFigure) getOwner();
        final Dimension2DDouble oldValue = originalArc2D;
        final Dimension2DDouble newValue = odgRect.getArc();
        view.getDrawing().fireUndoableEditHappened(new AbstractUndoableEdit() {
            public String getPresentationName() {
                ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.odg.Labels");
                return labels.getString("arc");
            }
            public void undo() throws CannotUndoException {
                super.undo();
                odgRect.willChange();
                odgRect.setArc(oldValue);
                odgRect.changed();
            }
            public void redo() throws CannotRedoException {
                super.redo();
                odgRect.willChange();
                odgRect.setArc(newValue);
                odgRect.changed();
            }
        });
    }
    public String getToolTipText(Point p) {
        return ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels").//
                getString("handle.roundRectangleRadius.toolTipText");
    }
}
