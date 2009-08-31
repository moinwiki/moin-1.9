/*
 * @(#)ChopEllipseConnector.java
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

import java.awt.*;
import java.awt.geom.*;
import static org.jhotdraw.draw.AttributeKeys.*;
import org.jhotdraw.geom.*;
/**
 * A {@link Connector} which locates a connection point at the bounds
 * of any figure which has an elliptic shape, such as {@link EllipseFigure}.
 * <p>
 *
 * @author Werner Randelshofer
 * @version $Id: ChopEllipseConnector.java 536 2009-06-14 12:10:57Z rawcoder $
 */
public class ChopEllipseConnector extends ChopRectangleConnector {
    /** 
     * Only used for DOMStorable input.
     */
    public ChopEllipseConnector() {
    }
    
    public ChopEllipseConnector(Figure owner) {
        super(owner);
    }
    
    private Color getStrokeColor(Figure f) {
        return STROKE_COLOR.get(f);
    }
    private float getStrokeWidth(Figure f) {
        Double w = STROKE_WIDTH.get(f);
        return (w == null) ? 1f : w.floatValue();
    }

    protected Point2D.Double chop(Figure target, Point2D.Double from) {
        target =  getConnectorTarget(target);
        Rectangle2D.Double r = target.getBounds();
        if (getStrokeColor(target) != null) {
            double grow;
            switch (STROKE_PLACEMENT.get(target)) {
                case CENTER:
                 default :
                    grow = getStrokeTotalWidth(target) / 2d;
                    break;
                case OUTSIDE :
                    grow = getStrokeTotalWidth(target);
                    break;
                case INSIDE :
                    grow = 0f;
                    break;
            }
            Geom.grow(r, grow, grow);
        }
        double angle = Geom.pointToAngle(r, from);
        return Geom.ovalAngleToPoint(r, angle);
    }
}
