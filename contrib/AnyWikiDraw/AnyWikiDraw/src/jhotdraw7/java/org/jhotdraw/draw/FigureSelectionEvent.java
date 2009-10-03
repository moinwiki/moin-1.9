/*
 * @(#)FigureSelectionEvent.java
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

import java.util.*;

/**
 * An {@code EventObject} sent to {@link FigureSelectionListener}s.
 *
 * <hr>
 * <b>Design Patterns</b>
 *
 * <p><em>Observer</em><br>
 * Selection changes of {@code DrawingView} are observed by user interface
 * components which act on selected figures.<br>
 * Subject: {@link org.jhotdraw.draw.DrawingView}; Observer:
 * {@link FigureSelectionListener}; Event: {@link FigureSelectionEvent}.
 * <hr>
 *
 * @author Werner Randelshofer
 * @version $Id: FigureSelectionEvent.java 536 2009-06-14 12:10:57Z rawcoder $
 */
public class FigureSelectionEvent extends java.util.EventObject {
private Set<Figure> oldValue;
private Set<Figure> newValue;

    /** Creates a new instance. */
    public FigureSelectionEvent(DrawingView source, Set<Figure> oldValue, Set<Figure> newValue) {
        super(source);
        this.oldValue = oldValue;
        this.newValue = newValue;
    }
    
    public DrawingView getView() {
        return (DrawingView) source;
    }
    
    public Set<Figure> getOldSelection() {
        return oldValue;
    }
    public Set<Figure> getNewSelection() {
        return newValue;
    }
}
