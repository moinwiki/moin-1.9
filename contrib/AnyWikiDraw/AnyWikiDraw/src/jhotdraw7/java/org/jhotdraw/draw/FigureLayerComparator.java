/*
 * @(#)FigureLayerComparator.java
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
 * A {@code Comparator} used to sort figures by their layer property.
 *
 * @author  Werner Randelshofer
 * @version $Id: FigureLayerComparator.java 536 2009-06-14 12:10:57Z rawcoder $
 */
public class FigureLayerComparator implements Comparator<Figure> {
    public final static FigureLayerComparator INSTANCE = new FigureLayerComparator();
    
    /** Creates a new instance. */
    private FigureLayerComparator() {
    }
    
    public int compare(Figure f1, Figure f2) {
        return f1.getLayer() - f2.getLayer();
    }
    
}
