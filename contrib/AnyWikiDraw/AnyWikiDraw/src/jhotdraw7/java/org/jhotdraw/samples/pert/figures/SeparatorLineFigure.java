/*
 * @(#)SeparatorLineFigure.java
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

package org.jhotdraw.samples.pert.figures;

import org.jhotdraw.util.*;
import java.awt.*;
import java.awt.geom.*;
import static org.jhotdraw.draw.AttributeKeys.*;
import org.jhotdraw.draw.LineFigure;
import org.jhotdraw.geom.*;
/**
 * A horizontal line with a preferred size of 1,1.
 *
 * @author  Werner Randelshofer
 * @version $Id: SeparatorLineFigure.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class SeparatorLineFigure 
extends LineFigure {
    
    /** Creates a new instance. */
    public SeparatorLineFigure() {
    }

    public void setBounds(Point2D.Double anchor, Point2D.Double lead) {
        setPoint(0, 0, anchor);
        setPoint(getNodeCount() - 1, 0, new Point2D.Double(lead.x, anchor.y));
    }
    public Dimension2DDouble getPreferredSize() {
        double width = Math.ceil(STROKE_WIDTH.get(this));
        return new Dimension2DDouble(width, width);
    }
}
