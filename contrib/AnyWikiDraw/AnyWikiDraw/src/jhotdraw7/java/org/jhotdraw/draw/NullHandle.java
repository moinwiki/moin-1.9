/*
 * @(#)NullHandle.java
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
 * A handle that doesn't change the owned figure. Its only purpose is
 * to show feedback that a figure is selected.
 *
 * @author Werner Randelshofer
 * @version $Id: NullHandle.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class NullHandle extends LocatorHandle {
    
    /** Creates a new instance. */
    public NullHandle(Figure owner, Locator locator) {
        super(owner, locator);
    }
    
    public Cursor getCursor() {
        return Cursor.getDefaultCursor();
    }
    
    public void trackStart(Point anchor, int modifiersEx) {
        
    }
    public void trackStep(Point anchor, Point lead, int modifiersEx) {
        
    }
    public void trackEnd(Point anchor, Point lead, int modifiersEx) {
        
    }
    
    /**
     * Creates handles for each lead of a
     * figure and adds them to the provided collection.
     */
    static public void addLeadHandles(Figure f, Collection<Handle> handles) {
        handles.add(new NullHandle(f, new RelativeLocator(0f,0f)));
        handles.add(new NullHandle(f, new RelativeLocator(0f,1f)));
        handles.add(new NullHandle(f, new RelativeLocator(1f,0f)));
        handles.add(new NullHandle(f, new RelativeLocator(1f,1f)));
    }
    /**
     * Draws this handle.
     * Null Handles are drawn as unfilled rectangles.
     */
    public void draw(Graphics2D g) {
        drawRectangle(g, 
                (Color) getEditor().getHandleAttribute(HandleAttributeKeys.NULL_HANDLE_FILL_COLOR),
                (Color) getEditor().getHandleAttribute(HandleAttributeKeys.NULL_HANDLE_STROKE_COLOR)
                );
    }
    
}
