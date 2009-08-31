/*
 * @(#)FontSizeLocator.java
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

/**
 * {@code FontSizeLocator} is used by {@link FontSizeHandle} to locate
 * its position on the drawing.
 *
 * @author  Werner Randelshofer
 * @version $Id: FontSizeLocator.java 536 2009-06-14 12:10:57Z rawcoder $
 */
public class FontSizeLocator implements Locator {
    
    /** Creates a new instance. */
    public FontSizeLocator() {
    }
    
    /**
     * Locates a position on the provided figure.
     * @return a Point2D.Double on the figure.
     */
    public Point2D.Double locate(Figure owner) {
        Point2D.Double p = (Point2D.Double) owner.getStartPoint().clone();
        
        if (owner instanceof TextHolderFigure) {
            p.y += ((TextHolderFigure) owner).getFontSize();
            p.y += ((TextHolderFigure) owner).getInsets().top;
        } else {
            p.y += FONT_SIZE.get(owner);
        }
        
        if (TRANSFORM.get(owner) != null) {
            TRANSFORM.get(owner).transform(p, p);
        }
        
        return p;
    }
    
    public Point2D.Double locate(Figure owner, Figure dependent) {
        return locate(owner);
    }
    
}
