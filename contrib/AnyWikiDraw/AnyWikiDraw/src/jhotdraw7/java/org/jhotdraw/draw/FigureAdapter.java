/*
 * @(#)FigureAdapter.java
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

/**
 * An abstract adapter class for receiving {@link FigureEvent}s. This class
 * exists as a convenience for creating {@link FigureListener} objects.
 * 
 * @author Werner Randelshofer
 * @version $Id: FigureAdapter.java 531 2009-06-13 10:20:39Z rawcoder $
 */
public class FigureAdapter implements FigureListener {
    public void areaInvalidated(FigureEvent e) {
    }
    
    public void attributeChanged(FigureEvent e) {
    }
    
    public void figureAdded(FigureEvent e) {
    }
    
    public void figureChanged(FigureEvent e) {
    }
    
    public void figureRemoved(FigureEvent e) {
    }
    
    public void figureRequestRemove(FigureEvent e) {
    }

    public void figureHandlesChanged(FigureEvent e) {
    }
    
}
