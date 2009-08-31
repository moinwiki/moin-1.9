/*
 * @(#)RGBColorSystem.java
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
 * A ColorSystem for RGB color components (red, green, blue).
 *
 * @author  Werner Randelshofer
 * @version $Id: RGBColorSystem.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class RGBColorSystem extends AbstractColorSystem {

    /**
     * Creates a new instance.
     */
    public RGBColorSystem() {
    }

    public float[] toComponents(int r, int g, int b, float[] components) {
        if (components == null || components.length != 3) {
            components = new float[3];
        }
        components[0] = r / 255f;
        components[1] = g / 255f;
        components[2] = b / 255f;
        return components;
    }

    public int toRGB(float... components) {
        return 0xff000000 | 
                ((int) (components[0] * 255) << 16) | 
                ((int) (components[1] * 255) << 8) | 
                (int) (components[2] * 255);
    }

    public int getComponentCount() {
        return 3;
    }
}
