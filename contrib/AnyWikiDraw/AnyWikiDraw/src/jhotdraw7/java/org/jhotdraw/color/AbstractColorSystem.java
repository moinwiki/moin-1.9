/*
 * @(#)AbstractColorSystem.java
 *
 * Copyright (c) 2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.color;

/**
 * Abstract super class for ColorSystem's.
 *
 * @author  Werner Randelshofer
 * @version $Id: AbstractColorSystem.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public abstract class AbstractColorSystem implements ColorSystem {
    public float[] toComponents(int rgb, float[] components) {
        return toComponents((rgb & 0xff0000) >> 16, (rgb & 0xff00) >> 8, rgb & 0xff, components);
    }
    
    public abstract float[] toComponents(int r, int g, int b, float[] components);
}
