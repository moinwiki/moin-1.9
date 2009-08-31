/*
 * @(#)ChopRectangleConnector.java
 *
 * Copyright (c) 1996-2007 by the original authors of JHotDraw
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
import static org.jhotdraw.draw.AttributeKeys.*;
import org.jhotdraw.geom.*;
/**
 * A {@link Connector} which locates a connection point at the bounds
 * of any figure which has a rectangular shape, such as {@link RectangleFigure}.
 * <p>
 * XXX - Replace all Chop...Connectors by a single ChopToCenterConnector and
 * move method chop(Point2D.Double) into Figure interface.
 *
 * @see Connector
 *
 * @author Werner Randelshofer
 * @version $Id: ChopRectangleConnector.java 536 2009-06-14 12:10:57Z rawcoder $
 */
public class ChopRectangleConnector extends AbstractConnector {
    
    
    /** Creates a new instance.
     * Only used for storable.
     */
    public ChopRectangleConnector() {
    }
    
    public ChopRectangleConnector(Figure owner) {
        super(owner);
    }
    
    @Override
    public Point2D.Double findStart(ConnectionFigure connection) {
        Figure startFigure = connection.getStartConnector().getOwner();
        Point2D.Double from;
        if (connection.getNodeCount() <= 2 || connection.getLiner() != null) {
            if (connection.getEndConnector() == null) {
                from = connection.getEndPoint();
            } else {
                Rectangle2D.Double r1 = getConnectorTarget(connection.getEndConnector().getOwner()).getBounds();
                from = new Point2D.Double(r1.x + r1.width/2, r1.y + r1.height/2);
            }
        } else {
            from = connection.getPoint(1);
        }
        return chop(startFigure, from);
    }
    
    @Override
    public Point2D.Double findEnd(ConnectionFigure connection) {
        Figure endFigure = connection.getEndConnector().getOwner();
        Point2D.Double from;
        if (connection.getNodeCount() <= 3 && connection.getStartFigure() == connection.getEndFigure() ||
                connection.getNodeCount() <= 2 ||
                connection.getLiner() != null) {
            if (connection.getStartConnector() == null) {
                from = connection.getStartPoint();
            } else if (connection.getStartFigure() == connection.getEndFigure()) {
                Rectangle2D.Double r1 = getConnectorTarget(connection.getStartConnector().getOwner()).getBounds();
                from = new Point2D.Double(r1.x + r1.width/2, r1.y);
            } else {
                Rectangle2D.Double r1 = getConnectorTarget(connection.getStartConnector().getOwner()).getBounds();
                from = new Point2D.Double(r1.x + r1.width/2, r1.y + r1.height/2);
            }
        } else {
            from = connection.getPoint(connection.getNodeCount() - 2);
        }
        
        return chop(endFigure, from);
    }
    
    protected Point2D.Double chop(Figure target, Point2D.Double from) {
        target = getConnectorTarget(target);
        Rectangle2D.Double r = target.getBounds();
        if (STROKE_COLOR.get(target) != null) {
            double grow;
            switch (STROKE_PLACEMENT.get(target)) {
                case CENTER:
                default :
                    grow = AttributeKeys.getStrokeTotalWidth(target) / 2d;
                    break;
                case OUTSIDE :
                    grow = AttributeKeys.getStrokeTotalWidth(target);
                    break;
                case INSIDE :
                    grow = 0d;
                    break;
            }
            Geom.grow(r, grow, grow);
        }
        return Geom.angleToPoint(r, Geom.pointToAngle(r, from));
    }
    
}
