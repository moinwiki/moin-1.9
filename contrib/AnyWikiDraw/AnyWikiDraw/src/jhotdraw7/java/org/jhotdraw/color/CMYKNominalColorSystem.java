/*
 * @(#)CMYKNominalColorSystem.java
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
 * A ColorSystem for CMYK color components (cyan, magenta, yellow, black) with
 * nominally converted color components from/to an RGB color model.
 * <p>
 * This model may not be very useful. It assumes that the color components 
 * perfectly absorb the desired wavelenghts.
 *
 * @author  Werner Randelshofer
 * @version $Id: CMYKNominalColorSystem.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class CMYKNominalColorSystem extends AbstractColorSystem {
    /**
     * Creates a new instance.
     */
    public CMYKNominalColorSystem() {
    }
    
    public float[] toComponents(int r, int g, int b, float[] component) {
        if (component == null || component.length != 4) {
            component = new float[4];
        }
        float cyan, magenta, yellow, black;
        
        cyan = 1f - r / 255f;
        magenta = 1f - g / 255f;
        yellow = 1f - b / 255f;
        if (Math.min(Math.min(cyan, magenta), yellow) >= 1f) {
            cyan = magenta = yellow = 0f;
            black = 1f;
        } else {
            black = Math.min(Math.min(cyan, magenta), yellow);
            
            if (black > 0f) {
                cyan = (cyan - black) / (1 - black);
                magenta = (magenta - black) / (1 - black);
                yellow = (yellow - black) / (1 - black);
            }
        }

        component[0] = cyan;
        component[1] = magenta;
        component[2] = yellow;
        component[3] = black;
        return component;
    }

    public int toRGB(float... component) {
        float cyan, magenta, yellow, black;
        
        cyan = component[0];
        magenta = component[1];
        yellow = component[2];
        black = component[3];
        
        float red, green, blue;
        red = 1f - cyan * (1f - black) - black;
        green = 1f - magenta * (1f - black) - black;
        blue = 1f - yellow * (1f - black) - black;
        return 0xff000000
        | ((int) (red * 255) << 16)
        | ((int) (green * 255) << 8)
        | (int) (blue * 255);
    }

    public int getComponentCount() {
        return 4;
    }
}
