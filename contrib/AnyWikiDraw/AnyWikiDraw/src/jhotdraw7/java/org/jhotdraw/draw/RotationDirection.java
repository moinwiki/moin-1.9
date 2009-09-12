/**
 * @(#)RotationDirection.java
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

/**
 * Specifies the possible directions for rotations on a two-dimensional plane.
 * <p>
 * This enumeration is used by drawing tools and handles to perform constrained
 * transforms of figures on a drawing.
 *
 * @see Constrainer
 * 
 * @author Werner Randelshofer
 * @version $Id: RotationDirection.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public enum RotationDirection {
    CLOCKWISE,
    COUNTER_CLOCKWISE
}
