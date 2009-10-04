/*
 * @(#)Shapes.java
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

package org.jhotdraw.geom;

import java.awt.*;
import java.awt.geom.*;

/**
 * Shapes.
 *
 * @author Werner Randelshofer
 * @version $Id: Shapes.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class Shapes {
    
    /** Creates a new instance. */
    private Shapes() {
    }
    
    /**
     * Returns true, if the outline of this bezier path contains the specified
     * point.
     *
     * @param p The point to be tested.
     * @param tolerance The tolerance for the test.
     */
    public static boolean outlineContains(Shape shape, Point2D.Double p, double tolerance) {
        PathIterator i = shape.getPathIterator(new AffineTransform(), tolerance);
        if (! i.isDone()) {
            double[] coords = new double[6];
            int type = i.currentSegment(coords);
            double prevX = coords[0];
            double prevY = coords[1];
            i.next();
            while (! i.isDone()) {
                i.currentSegment(coords);
                if (Geom.lineContainsPoint(
                        prevX, prevY, coords[0], coords[1],
                        p.x, p.y, tolerance)
                        ) {
                    return true;
                }
                prevX = coords[0];
                prevY = coords[1];
                i.next();
            }
        }
        return false;
    }
    
}
