/*
 * @(#)ChopBezierConnector.java
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
/**
 * A {@link Connector} which locates a connection point at the bounds
 * of a {@link BezierFigure}.
 * <p>
 * <p>
 * XXX - This connector does not take the stroke width of the polygon into
 * account.
 * 
 * 
 * @author Werner Randelshofer
 * @version $Id: ChopBezierConnector.java 536 2009-06-14 12:10:57Z rawcoder $
 */
public class ChopBezierConnector extends ChopRectangleConnector {
    
    /** Creates a new instance. */
    public ChopBezierConnector() {
    }
    
    public ChopBezierConnector(BezierFigure owner) {
        super(owner);
    }
    
    protected Point2D.Double chop(Figure target, Point2D.Double from) {
        BezierFigure bf = (BezierFigure) getConnectorTarget(target);
        return bf.chop(from);
    }
}
