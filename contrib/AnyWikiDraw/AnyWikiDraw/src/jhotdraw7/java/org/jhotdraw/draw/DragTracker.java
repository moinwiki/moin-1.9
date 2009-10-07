/*
 * @(#)DragTracker.java
 * 
 * Copyright (c) 2009 by the original authors of JHotDraw
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
 * A <em>drag tracker</em> provides the behavior for dragging selected
 * figures to the {@link SelectionTool}.
 *
 * <hr>
 * <b>Design Patterns</b>
 *
 * <p><em>Strategy</em><br>
 * The different behavior states of the selection tool are implemented by
 * trackers.<br>
 * Context: {@link SelectionTool}; State: {@link DragTracker},
 * {@link HandleTracker}, {@link SelectAreaTracker}.
 *
 * <p><em>Chain of responsibility</em><br>
 * Mouse and keyboard events of the user occur on a drawing view, and are
 * preprocessed by the {@code DragTracker} of a {@code SelectionTool}. {@code
 * DragTracker} invokes "track" methods on a {@code Handle} which in turn
 * changes an aspect of a figure.
 * Client: {@link SelectionTool}; Handler: {@link DragTracker}, {@link Handle}.
 * <hr>
 *
 *
 * @author Werner Randelshofer
 * @version $Id: DragTracker.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public interface DragTracker extends Tool {

    public void setDraggedFigure(Figure f);

}
