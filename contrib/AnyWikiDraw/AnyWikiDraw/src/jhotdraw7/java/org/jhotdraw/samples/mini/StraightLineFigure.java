/*
 * @(#)StraightLineFigure.java
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

package org.jhotdraw.samples.mini;

import java.awt.*;
import java.awt.geom.*;
import org.jhotdraw.draw.*;
import org.jhotdraw.geom.*;

/**
 * Example showing the minimal amount of code needed to implement a
 * {@code Figure} by extending {@code AbstractAttributedFigure}.
 *
 * @author Werner Randelshofer
 * @version $Id: StraightLineFigure.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class StraightLineFigure extends AbstractAttributedFigure {
    private Line2D.Double line;
    
    /** Creates a new instance. */
    public StraightLineFigure() {
        line = new Line2D.Double();
    }

    protected void drawFill(Graphics2D g) {
    }

    protected void drawStroke(Graphics2D g) {
        g.draw(line);
    }

    public void transform(AffineTransform ty) {
        Point2D.Double p1 = (Point2D.Double) line.getP1();
        Point2D.Double p2 = (Point2D.Double) line.getP2();
        line.setLine(
                ty.transform(p1, p1),
                ty.transform(p2, p2)
                );
    }

    public void setBounds(Point2D.Double start, Point2D.Double end) {
        line.setLine(start, end);
    }

    public Rectangle2D.Double getBounds() {
        return (Rectangle2D.Double) line.getBounds2D();
    }

    public Object getTransformRestoreData() {
        return line.clone();
    }

    public void restoreTransformTo(Object restoreData) {
        line = (Line2D.Double) ((Line2D.Double) restoreData).clone();
    }

    public boolean contains(Point2D.Double p) {
        return Geom.lineContainsPoint(
                line.x1,line.y1,
                line.x2, line.y2,
                p.x, p.y, 
                AttributeKeys.getStrokeTotalWidth(this));
    }
    
    public StraightLineFigure clone() {
        StraightLineFigure that = (StraightLineFigure) super.clone();
        that.line = (Line2D.Double) this.line.clone();
        return that;
    }
}
