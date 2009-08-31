/*
 * @(#)HandleListener.java
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

import java.util.*;
/**
 * Interface implemented by observers of {@link Handle}s.
 * <hr>
 * <b>Design Patterns</b>
 *
 * <p><em>Observer</em><br>
 * State changes of handles can be observed by other objects. Specifically
 * {@code DrawingView} observes area invalidations and remove requests of
 * handles.<br>
 * Subject: {@link Handle}; Observer: {@link HandleListener}; Event:
 * {@link HandleEvent}; Concrete Observer: {@link DrawingView}.
 * <hr>
 *
 * @author Werner Randelshofer
 * @version $Id: HandleListener.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public interface HandleListener extends EventListener {
    /**
     * Sent when an area of the drawing view needs to be repainted.
     */
    public void areaInvalidated(HandleEvent e);
    
    /**
     * Sent when requesting to remove a handle.
     */
    public void handleRequestRemove(HandleEvent e);
    /**
     * Sent when requesting to add secondary handles.
     */
    public void handleRequestSecondaryHandles(HandleEvent e);
}
