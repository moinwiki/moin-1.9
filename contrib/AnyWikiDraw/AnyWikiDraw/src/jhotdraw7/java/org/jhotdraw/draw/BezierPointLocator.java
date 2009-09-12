/*
 * @(#)BezierPointLocator.java
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
import org.jhotdraw.xml.*;

/**
 * A {@link Locator} which locates a node on the bezier path of a BezierFigure.
 * 
 * 
 * @author Werner Randelshofer
 * @version $Id: BezierPointLocator.java 532 2009-06-13 11:28:36Z rawcoder $
 */
public class BezierPointLocator extends AbstractLocator {
    private int index;
    private int coord;
    
    public BezierPointLocator(int index) {
        this.index = index;
        this.coord = 0;
    }
    public BezierPointLocator(int index, int coord) {
        this.index = index;
        this.coord = index;
    }
    
    public Point2D.Double locate(Figure owner) {
        BezierFigure plf = (BezierFigure) owner;
        if (index < plf.getNodeCount()) {
            return plf.getPoint(index, coord);
        }
        return new Point2D.Double(0, 0);
    }

    public void write(DOMOutput out) {
        out.addAttribute("index", index, 0);
        out.addAttribute("coord", coord, 0);
    }

    public void read(DOMInput in) {
       index = in.getAttribute("index", 0);
       coord = in.getAttribute("coord", 0);
    }
    
    
}
