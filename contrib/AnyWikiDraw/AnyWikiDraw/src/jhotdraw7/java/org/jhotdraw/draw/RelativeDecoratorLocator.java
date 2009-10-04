/*
 * @(#)RelativeLocator.java
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
/**
 * A locator that specfies a point that is relative to the bounds
 * of a figures decorator.
 *
 * @author Werner Randelshofer
 * @version $Id: RelativeDecoratorLocator.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class RelativeDecoratorLocator extends RelativeLocator {
    private boolean isQuadratic;
    
    public RelativeDecoratorLocator() {
    }
    
    /** Creates a new instance. */
    public RelativeDecoratorLocator(double relativeX, double relativeY) {
        super(relativeX, relativeY);
    }
    public RelativeDecoratorLocator(double relativeX, double relativeY, boolean isQuadratic) {
        super(relativeX, relativeY);
        this.isQuadratic = isQuadratic;
    }
    
    public java.awt.geom.Point2D.Double locate(Figure owner) {
        Rectangle2D.Double r;
        if ((owner instanceof DecoratedFigure) && 
                ((DecoratedFigure) owner).getDecorator() != null) {
            r = ((DecoratedFigure) owner).getDecorator().getBounds();
        } else {
            r = owner.getBounds();
        }
        if (isQuadratic) {
        double side = Math.max(r.width, r.height);
        r.x -= (side - r.width) / 2;
        r.y -= (side - r.height) / 2;
        r.width = r.height = side;
        }
        return new Point2D.Double(
                r.x + r.width * relativeX,
                r.y + r.height * relativeY
                );
    }
    
    static public Locator east() {
        return new RelativeDecoratorLocator(1.0, 0.5);
    }
    
    /**
     * North.
     */
    static public Locator north() {
        return new RelativeDecoratorLocator(0.5, 0.0);
    }
    
    /**
     * West.
     */
    static public Locator west() {
        return new RelativeDecoratorLocator(0.0, 0.5);
    }
    
    /**
     * North east.
     */
    static public Locator northEast() {
        return new RelativeDecoratorLocator(1.0, 0.0);
    }
    
    /**
     * North west.
     */
    static public Locator northWest() {
        return new RelativeDecoratorLocator(0.0, 0.0);
    }
    
    /**
     * South.
     */
    static public Locator south() {
        return new RelativeDecoratorLocator(0.5, 1.0);
    }
    
    /**
     * South east.
     */
    static public Locator southEast() {
        return new RelativeDecoratorLocator(1.0, 1.0);
    }
    
    /**
     * South west.
     */
    static public Locator southWest() {
        return new RelativeDecoratorLocator(0.0, 1.0);
    }
    
    /**
     * Center.
     */
    static public Locator center() {
        return new RelativeDecoratorLocator(0.5, 0.5);
    }
}
