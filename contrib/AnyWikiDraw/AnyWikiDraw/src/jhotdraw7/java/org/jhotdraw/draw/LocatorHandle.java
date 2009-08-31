/*
 * @(#)LocatorHandle.java
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
 * A LocatorHandle implements a Handle by delegating the location requests to
 * a Locator object.
 *
 * @see Locator
 *
 * @author Werner Randelshofer
 * @version $Id: LocatorHandle.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public abstract class LocatorHandle extends AbstractHandle {
    private Locator locator;
    
    /**
     * Initializes the LocatorHandle with the given Locator.
     */
    public LocatorHandle(Figure owner, Locator l) {
        super(owner);
        locator = l;
    }
    
    public Point2D.Double getLocationOnDrawing() {
        return locator.locate(getOwner());
    }
    
    public Point getLocation() {
        return view.drawingToView(locator.locate(getOwner()));
    }
    
    protected Rectangle basicGetBounds() {
        Rectangle r = new Rectangle(getLocation());
        int h = getHandlesize();
        r.x -= h / 2;
        r.y -= h / 2;
        r.width = r.height = h;
        return r;
    }
}
