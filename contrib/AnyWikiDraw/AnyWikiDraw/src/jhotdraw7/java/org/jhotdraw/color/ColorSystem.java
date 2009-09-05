/**
 * @(#)ColorSystem.java
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
 * A ColorSystem defines a system to describe colors using a number of
 * components. Each component has a normalized value between 0 and 1.
 *
 * @author Werner Randelshofer
 * @version $Id: ColorSystem.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public interface ColorSystem {
    /**
     * Returns the number of color components used by the color system.
     * 
     * @return component count.
     */
    public int getComponentCount();
    
    /**
     * Converts the specified color components to RGB.
     * 
     * @param components The color components.
     * 
     * @return rgb value.
     */
    public int toRGB(float... components);
    /**
     * Converts the specified color components to RGB.
     * 
     * @param rgb value.
     * @param components A component array for reuse.
     * 
     * @return color components for the rgb value.
     */
    public float[] toComponents(int rgb, float[] components);
    
}
