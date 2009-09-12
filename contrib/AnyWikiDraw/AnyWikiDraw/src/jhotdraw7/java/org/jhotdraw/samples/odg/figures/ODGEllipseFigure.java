/*
 * @(#)ODGEllipse.java
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

import java.awt.*;
import java.awt.event.*;
import java.awt.geom.*;
import java.io.*;
import java.util.*;
import javax.swing.*;
import org.jhotdraw.draw.*;
import static org.jhotdraw.samples.odg.ODGAttributeKeys.*;
import org.jhotdraw.geom.*;
import org.jhotdraw.samples.odg.*;
import org.jhotdraw.samples.odg.ODGConstants;
import org.jhotdraw.xml.*;
import org.jhotdraw.util.*;
/**
 * ODGEllipse represents a ODG ellipse and a ODG circle element.
 *
 * @author Werner Randelshofer
 * @version $Id: ODGEllipseFigure.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ODGEllipseFigure extends ODGAttributedFigure implements ODGFigure {
    private Ellipse2D.Double ellipse;
    /**
     * This is used to perform faster drawing and hit testing.
     */
    private transient Shape cachedTransformedShape;
    
    /** Creates a new instance. */
    public ODGEllipseFigure() {
        this(0, 0, 0, 0);
    }
    
    public ODGEllipseFigure(double x, double y, double width, double height) {
        ellipse = new Ellipse2D.Double(x, y, width, height);
        ODGAttributeKeys.setDefaults(this);
    }
    
    // DRAWING
    protected void drawFill(Graphics2D g) {
        g.fill(ellipse);
        //g.fill(getTransformedShape());
    }
    
    protected void drawStroke(Graphics2D g) {
        g.draw(ellipse);
        /*
        if (TRANSFORM.get(this) == null) {
            g.draw(ellipse);
        } else {
            AffineTransform savedTransform = g.getTransform();
            g.transform(TRANSFORM.get(this));
            g.draw(ellipse);
            g.setTransform(savedTransform);
        }*/
    }
    // SHAPE AND BOUNDS
    public double getX() {
        return ellipse.x;
    }
    public double getY() {
        return ellipse.y;
    }
    public double getWidth() {
        return ellipse.getWidth();
    }
    public double getHeight() {
        return ellipse.getHeight();
    }
    
    public Rectangle2D.Double getBounds() {
        return (Rectangle2D.Double) ellipse.getBounds2D();
    }
    @Override public Rectangle2D.Double getDrawingArea() {
        Rectangle2D rx = getTransformedShape().getBounds2D();
        Rectangle2D.Double r = (rx instanceof Rectangle2D.Double) ? (Rectangle2D.Double) rx : new Rectangle2D.Double(rx.getX(), rx.getY(), rx.getWidth(), rx.getHeight());
        if (TRANSFORM.get(this) == null) {
            double g = ODGAttributeKeys.getPerpendicularHitGrowth(this) * 2;
            Geom.grow(r, g, g);
        } else {
            double strokeTotalWidth = AttributeKeys.getStrokeTotalWidth(this);
            double width = strokeTotalWidth / 2d;
            width *= Math.max(TRANSFORM.get(this).getScaleX(), TRANSFORM.get(this).getScaleY());
            Geom.grow(r, width, width);
        }
        return r;
    }
    /**
     * Checks if a Point2D.Double is inside the figure.
     */
    public boolean contains(Point2D.Double p) {
        // XXX - This does not take the stroke width into account!
        return getTransformedShape().contains(p);
    }
    private Shape getTransformedShape() {
        if (cachedTransformedShape == null) {
            if (TRANSFORM.get(this) == null) {
                cachedTransformedShape = ellipse;
            } else {
                cachedTransformedShape = TRANSFORM.get(this).createTransformedShape(ellipse);
            }
        }
        return cachedTransformedShape;
    }
    public void setBounds(Point2D.Double anchor, Point2D.Double lead) {
        ellipse.x = Math.min(anchor.x, lead.x);
        ellipse.y = Math.min(anchor.y , lead.y);
        ellipse.width = Math.max(0.1, Math.abs(lead.x - anchor.x));
        ellipse.height = Math.max(0.1, Math.abs(lead.y - anchor.y));
    }
    /**
     * Transforms the figure.
     *
     * @param tx the transformation.
     */
    public void transform(AffineTransform tx) {
        if (TRANSFORM.get(this) != null ||
                (tx.getType() & (AffineTransform.TYPE_TRANSLATION)) != tx.getType()) {
            if (TRANSFORM.get(this) == null) {
                TRANSFORM.basicSetClone(this, tx);
            } else {
                AffineTransform t = TRANSFORM.getClone(this);
                t.preConcatenate(tx);
                TRANSFORM.basicSet(this, t);
            }
        } else {
            Point2D.Double anchor = getStartPoint();
            Point2D.Double lead = getEndPoint();
            setBounds(
                    (Point2D.Double) tx.transform(anchor, anchor),
                    (Point2D.Double) tx.transform(lead, lead)
                    );
            if (FILL_GRADIENT.get(this) != null && 
                    ! FILL_GRADIENT.get(this).isRelativeToFigureBounds()) {
                Gradient g = FILL_GRADIENT.getClone(this);
                g.transform(tx);
                FILL_GRADIENT.basicSet(this, g);
            }
            if (STROKE_GRADIENT.get(this) != null &&
                    ! STROKE_GRADIENT.get(this).isRelativeToFigureBounds()) {
                Gradient g = STROKE_GRADIENT.getClone(this);
                g.transform(tx);
                STROKE_GRADIENT.basicSet(this, g);
            }
        }
        invalidate();
    }
    public void restoreTransformTo(Object geometry) {
        Object[] restoreData = (Object[]) geometry;
        ellipse = (Ellipse2D.Double) ((Ellipse2D.Double) restoreData[0]).clone();
        TRANSFORM.basicSetClone(this, (AffineTransform) restoreData[1]);
            FILL_GRADIENT.basicSetClone(this, (Gradient) restoreData[2]);
            STROKE_GRADIENT.basicSetClone(this, (Gradient) restoreData[3]);
        invalidate();
    }
    
    public Object getTransformRestoreData() {
        return new Object[] {
            ellipse.clone(),
            TRANSFORM.getClone(this),
            FILL_GRADIENT.getClone(this),
            STROKE_GRADIENT.getClone(this),
        };
    }
    
    
    // ATTRIBUTES
    // EDITING
    @Override public Collection<Handle> createHandles(int detailLevel) {
        LinkedList<Handle> handles = new LinkedList<Handle>();
        switch (detailLevel % 2) {
            case 0 :
                ResizeHandleKit.addResizeHandles(this, handles);
                break;
            case 1 :
                TransformHandleKit.addTransformHandles(this, handles);
                break;
            default:
                break;
        }
        return handles;
    }
    // CONNECTING
    public boolean canConnect() {
        return false; // ODG does not support connecting
    }
    public Connector findConnector(Point2D.Double p, ConnectionFigure prototype) {
        return null; // ODG does not support connectors
    }
    public Connector findCompatibleConnector(Connector c, boolean isStartConnector) {
        return null; // ODG does not support connectors
    }
    // COMPOSITE FIGURES
    // CLONING
    public ODGEllipseFigure clone() {
        ODGEllipseFigure that = (ODGEllipseFigure) super.clone();
        that.ellipse = (Ellipse2D.Double) this.ellipse.clone();
        that.cachedTransformedShape = null;
        return that;
    }
    
    // EVENT HANDLING
    public boolean isEmpty() {
        Rectangle2D.Double b = getBounds();
        return b.width <= 0 || b.height <= 0;
    }
    @Override public void invalidate() {
        super.invalidate();
        cachedTransformedShape = null;
    }
}
