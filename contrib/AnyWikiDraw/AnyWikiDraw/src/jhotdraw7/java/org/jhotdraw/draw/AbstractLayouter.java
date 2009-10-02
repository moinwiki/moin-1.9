/*
 * @(#)AbstractLayouter.java
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
 * This abstract class can be extended to implement a {@link Layouter}
 * which has its own attribute set.
 *
 * @author  Werner Randelshofer
 * @version $Id: AbstractLayouter.java 531 2009-06-13 10:20:39Z rawcoder $
 */
public abstract class AbstractLayouter implements Layouter {
    
    public Insets2D.Double getInsets(Figure child) {
        Insets2D.Double value =  CompositeFigure.LAYOUT_INSETS.get(child);
        return (value == null) ? new Insets2D.Double() : (Insets2D.Double) value.clone();
    }
}
