/*
 * @(#)ConnectionStartHandle.java
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

/**
 * A {@link Handle} which allows to connect the start of a
 * {@link ConnectionFigure} to another figure.
 *
 * @author Werner Randelshofer
 * @version $Id: ConnectionStartHandle.java 536 2009-06-14 12:10:57Z rawcoder $
 */
public class ConnectionStartHandle extends AbstractConnectionHandle {
    
    /**
     * Constructs the connection handle for the given start figure.
     */
    public ConnectionStartHandle(ConnectionFigure owner) {
        super(owner);
    }
    
    /**
     * Sets the start of the connection.
     */
    protected void connect(Connector c) {
        getOwner().setStartConnector(c);
    }
    
    /**
     * Disconnects the start figure.
     */
    protected void disconnect() {
        getOwner().setStartConnector(null);
    }
    
    
    protected Connector getTarget() {
        return getOwner().getStartConnector();
    }
    
    /**
     * Sets the start point of the connection.
     */
    protected void setLocation(Point2D.Double p) {
        getOwner().willChange();
        getOwner().setStartPoint(p);
        getOwner().changed();
    }
    
    /**
     * Returns the start point of the connection.
     */
    protected Point2D.Double getLocation() {
        return getOwner().getStartPoint();
    }
    
    protected boolean canConnect(Connector existingEnd, Connector targetEnd) {
        return getOwner().canConnect(targetEnd, existingEnd);
    }

    protected int getBezierNodeIndex() {
        return 0;
    }
    
}