/*
 * @(#)GroupFigure.java
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
import org.jhotdraw.geom.*;

/**
 * A {@link Figure} which groups a collection of figures.
 *
 * @author Werner Randelshofer
 * @version $Id: GroupFigure.java 531 2009-06-13 10:20:39Z rawcoder $
 */
public class GroupFigure extends AbstractCompositeFigure {
    /** Creates a new instance. */
    public GroupFigure() {
    }
    
    public boolean canConnect() {
        return true;
    }
    
    /**
     * This is a default implementation that chops the point at the rectangle
     * returned by getBounds() of the figure.
     * <p>
     * Figures which have a non-rectangular shape need to override this method.
     * <p>
     * FIXME Invoke chop on each child and return the closest point.
     */
    public Point2D.Double chop(Point2D.Double from) {
        Rectangle2D.Double r = getBounds();
        return Geom.angleToPoint(r, Geom.pointToAngle(r, from));
    }
}
