/*
 * @(#)EllipseFigure.java
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

import org.jhotdraw.geom.Geom;
import java.awt.*;
import java.awt.geom.*;
import static org.jhotdraw.draw.AttributeKeys.*;

/**
 * A {@link Figure} with an elliptic shape.
 *
 * @author Werner Randelshofer
 * @version $Id: EllipseFigure.java 531 2009-06-13 10:20:39Z rawcoder $
 */
public class EllipseFigure extends AbstractAttributedFigure {
    protected Ellipse2D.Double ellipse;
    
    /** Creates a new instance. */
    public EllipseFigure() {
        this(0, 0, 0, 0);
    }
    
    public EllipseFigure(double x, double y, double width, double height) {
        ellipse = new Ellipse2D.Double(x, y, width, height);
        /*
        setFillColor(Color.white);
        setStrokeColor(Color.black);
         */
        setAttributeEnabled(TEXT_COLOR, false);
    }
    
    // DRAWING
    // SHAPE AND BOUNDS
    // ATTRIBUTES
    // EDITING
    // CONNECTING
    @Override
    public Connector findConnector(Point2D.Double p, ConnectionFigure prototype) {
        return new ChopEllipseConnector(this);
    }
    @Override
    public Connector findCompatibleConnector(Connector c, boolean isStartConnector) {
        return new ChopEllipseConnector(this);
    }
    // COMPOSITE FIGURES
    // CLONING
    // EVENT HANDLING
    public Rectangle2D.Double getBounds() {
        return (Rectangle2D.Double) ellipse.getBounds2D();
    }
    public Rectangle2D.Double getDrawingArea() {
        Rectangle2D.Double r = (Rectangle2D.Double) ellipse.getBounds2D();
        double grow = AttributeKeys.getPerpendicularHitGrowth(this);
        Geom.grow(r, grow, grow);
        return r;
    }
    
    protected void drawFill(Graphics2D g) {
        Ellipse2D.Double r = (Ellipse2D.Double) ellipse.clone();
        double grow = AttributeKeys.getPerpendicularFillGrowth(this);
        r.x -= grow;
        r.y -= grow;
        r.width += grow * 2;
        r.height += grow * 2;
        if (r.width > 0 && r.height > 0) {
            g.fill(r);
        }
    }
    
    protected void drawStroke(Graphics2D g) {
        Ellipse2D.Double r = (Ellipse2D.Double) ellipse.clone();
        double grow = AttributeKeys.getPerpendicularDrawGrowth(this);
        r.x -= grow;
        r.y -= grow;
        r.width += grow * 2;
        r.height += grow * 2;
        
        if (r.width > 0 && r.height > 0) {
            g.draw(r);
        }
    }
    
    /**
     * Checks if a Point2D.Double is inside the figure.
     */
    public boolean contains(Point2D.Double p) {
        Ellipse2D.Double r = (Ellipse2D.Double) ellipse.clone();
        double grow = AttributeKeys.getPerpendicularHitGrowth(this);
        r.x -= grow;
        r.y -= grow;
        r.width += grow * 2;
        r.height += grow * 2;
        
        return r.contains(p);
    }
    
    @Override
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
        Point2D.Double anchor = getStartPoint();
        Point2D.Double lead = getEndPoint();
        setBounds(
                (Point2D.Double) tx.transform(anchor, anchor),
                (Point2D.Double) tx.transform(lead, lead)
                );
    }
    
    @Override
    public EllipseFigure clone() {
        EllipseFigure that = (EllipseFigure) super.clone();
        that.ellipse = (Ellipse2D.Double) this.ellipse.clone();
        return that;
    }
    
    public void restoreTransformTo(Object geometry) {
        Ellipse2D.Double r = (Ellipse2D.Double) geometry;
        ellipse.x = r.x;
        ellipse.y = r.y;
        ellipse.width = r.width;
        ellipse.height = r.height;
    }
    
    public Object getTransformRestoreData() {
        return ellipse.clone();
    }
    
}