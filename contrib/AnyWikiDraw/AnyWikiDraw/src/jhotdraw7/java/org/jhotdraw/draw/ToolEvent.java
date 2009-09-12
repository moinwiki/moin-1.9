/*
 * @(#)ToolEvent.java
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
import java.util.*;

/**
 * An event sent to ToolListener's.
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
 * @version $Id: ToolEvent.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ToolEvent extends EventObject {
    private Rectangle invalidatedArea;
    private DrawingView view;
    
    /** Creates a new instance. */
    public ToolEvent(Tool src, DrawingView view, Rectangle invalidatedArea) {
        super(src);
        this.view = view;
        this.invalidatedArea = invalidatedArea;
    }
    
    /**
     * Gets the tool which is the source of the event.
     */
    public Tool getTool() {
        return (Tool) getSource();
    }
    /**
     * Gets the drawing view of the tool.
     */
    public DrawingView getView() {
        return view;
    }
    /**
     *  Gets the bounds of the invalidated area on the drawing view.
     */
    public Rectangle getInvalidatedArea() {
        return invalidatedArea;
    }
}
