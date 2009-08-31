/*
 * @(#)ToolListener.java
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
 * Interface implemented by observers of {@link Tool}s.
 * 
 * <hr>
 * <b>Design Patterns</b>
 *
 * <p><em>Observer</em><br>
 * State changes of tools can be observed by other objects. Specifically
 * {@code DrawingEditor} observes area invalidations of tools and repaints
 * its active drawing view accordingly.<br>
 * Subject: {@link Tool}; Observer: {@link ToolListener}; Event:
 * {@link ToolEvent}; Concrete Observer: {@link DrawingEditor}.
 * <hr>
 *
 * @author Werner Randelshofer
 * @version $Id: ToolListener.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public interface ToolListener extends EventListener {
    /**
     * Informs the listener that a tool has starteds interacting with a 
     * specific drawing view.
     */
    void toolStarted(ToolEvent event);
    /**
     * Informs the listener that a tool has done its interaction.
     * This method can be used to switch back to the default tool.
     */
    void toolDone(ToolEvent event);
    /**
     * Sent when an area of the drawing view needs to be repainted.
     */
    public void areaInvalidated(ToolEvent e);
    
}
