/*
 * @(#)ListFigure.java
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

import org.jhotdraw.geom.*;

/**
 * A ListFigure consists of a list of Figures and a RectangleFigure.
 *
 * @author  Werner Randelshofer
 * @version $Id: ListFigure.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ListFigure
extends GraphicalCompositeFigure {
    /** Creates a new instance. */
    public ListFigure() {
        this(null);
    }
    public ListFigure(Figure presentationFigure) {
        super(presentationFigure); 
        setLayouter(new VerticalLayouter());
        LAYOUT_INSETS.basicSet(this, new Insets2D.Double(4,8,4,8));
    }
}
