/*
 * @(#)GrowStroke.java
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

package org.jhotdraw.geom;

import java.awt.*;
import java.awt.geom.*;

/**
 * GrowStroke can be used to grow/shrink a figure by a specified line width.
 * This only works with closed convex paths having edges in clockwise direction.
 * <p>
 * Note: Although this is a Stroke object, it does not actually create a stroked
 * shape, but one that can be used for filling. 
 * 
 * @author Werner Randelshofer.
 * @version $Id: GrowStroke.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class GrowStroke extends DoubleStroke {
    private float grow;
    
    public GrowStroke(float grow, float miterLimit) {
        super(grow * 2f, 1f, BasicStroke.CAP_SQUARE, BasicStroke.JOIN_BEVEL, miterLimit, null, 0f);
   this.grow = grow;
    }
    
    public Shape createStrokedShape(Shape s) {

    BezierPath bp = new BezierPath();
        GeneralPath left = new GeneralPath();
        GeneralPath right = new GeneralPath();
        
        if (s instanceof GeneralPath) {
            left.setWindingRule(((GeneralPath) s).getWindingRule());
            right.setWindingRule(((GeneralPath) s).getWindingRule());
        } else if (s instanceof BezierPath) {
            left.setWindingRule(((BezierPath) s).getWindingRule());
            right.setWindingRule(((BezierPath) s).getWindingRule());
        }
        
        double[] coords = new double[6];
        // FIXME - We only do a flattened path
        for (PathIterator i = s.getPathIterator(null, 0.1d); ! i.isDone(); i.next()) {
            int type = i.currentSegment(coords);
            
            switch (type) {
                case PathIterator.SEG_MOVETO :
                    if (bp.size() != 0) {
                        traceStroke(bp, left, right);
                    }
                    bp.clear();
                    bp.moveTo(coords[0], coords[1]);
                    break;
                case PathIterator.SEG_LINETO :
                    if (coords[0] != bp.get(bp.size() - 1).x[0] ||
                            coords[1] != bp.get(bp.size() - 1).y[0]) {
                        bp.lineTo(coords[0], coords[1]);
                    }
                    break;
                case PathIterator.SEG_QUADTO :
                    bp.quadTo(coords[0], coords[1], coords[2], coords[3]);
                    break;
                case PathIterator.SEG_CUBICTO :
                    bp.curveTo(coords[0], coords[1], coords[2], coords[3], coords[4], coords[5]);
                    break;
                case PathIterator.SEG_CLOSE:
                    bp.setClosed(true);
                    break;
            }
        }
        if (bp.size() > 1) {
            traceStroke(bp, left, right);
        }
        
        
        if (Geom.contains(left.getBounds2D(),right.getBounds2D())) {
            return (grow > 0) ? left : right;
        } else {
            return (grow > 0) ? right : left;
        }
    }
    
}