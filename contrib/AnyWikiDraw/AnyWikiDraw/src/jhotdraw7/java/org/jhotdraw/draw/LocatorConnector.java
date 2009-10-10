/*
 * @(#)LocatorConnector.java
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
import java.io.IOException;
import org.jhotdraw.xml.*;
/**
 * A LocatorConnector locates connection points with
 * the help of a Locator. It supports the definition
 * of connection points to semantic locations.
 *
 * @see Locator
 * @see Connector
 *
 * @author Werner Randelshofer
 * @version $Id: LocatorConnector.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class LocatorConnector extends AbstractConnector {
    /**
     * The standard size of the connector. The display box
     * is centered around the located point.
     * <p>
     * FIXME - Why do we need a standard size?
     */
    public static final int SIZE = 2;
    
    private Locator  locator;
    
    /**
     * Creates a new instance.
     * Only used for DOMStorable.
     */
    public LocatorConnector() {
    }
    
    public LocatorConnector(Figure owner, Locator l) {
        super(owner);
        locator = l;
    }

    public Locator getLocator() {
        return locator;
    }

    protected Point2D.Double locate(ConnectionFigure connection) {
        return locator.locate(getOwner());
    }
    
    /**
     * Tests if a point is contained in the connector.
     */
    @Override public boolean contains(Point2D.Double p) {
        return getBounds().contains(p);
    }
    
    /**
     * Gets the display box of the connector.
     */
   @Override public Rectangle2D.Double getBounds() {
        Point2D.Double p = locator.locate(getOwner());
        return new Rectangle2D.Double(
        p.x - SIZE / 2,
        p.y - SIZE / 2,
        SIZE,
        SIZE);
    }
    
    @Override public void read(DOMInput in) throws IOException {
        super.read(in);
        in.openElement("locator");
        this.locator = (Locator) in.readObject(0);
        in.closeElement();
    }
    
   @Override public void write(DOMOutput out) throws IOException {
        super.write(out);
        out.openElement("locator");
        out.writeObject(locator);
        out.closeElement();
    }
}
