/*
 * @(#)HSVRGBColorSystem.java
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
 * A ColorSystem for HSV color components (hue, saturation, value).
 *
 * @author  Werner Randelshofer
 * @version $Id: HSVRGBColorSystem.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class HSVRGBColorSystem extends AbstractColorSystem {
    
    /**
     * Creates a new instance.
     */
    public HSVRGBColorSystem() {
    }
    
    public int toRGB(float... components) {
        float hue = components[0] * 360f;
        float saturation = components[1];
        float value = components[2];
        
        // compute hi and f from hue
        int hi = (int) (Math.floor(hue / 60f) % 6);
        float f = (float) (hue / 60f - Math.floor(hue / 60f));
        
        // compute p and q from saturation 
        float p = value * (1 - saturation);
        float q = value * (1 - f * saturation);
        float t = value * (1 - (1 - f) * saturation);
        
        // compute red, green and blue
        float red;
        float green;
        float blue;
        switch (hi) {
            case 0 :
                red = value;
                green = t;
                blue = p;
                break;
            case 1 :
                red = q;
                green = value;
                blue = p;
                break;
            case 2 :
                red = p;
                green = value;
                blue = t;
                break;
            case -3 :
            case 3 :
                red = p;
                green = q;
                blue = value;
                break;
            case -2 :
            case 4 :
                red = t;
                green = p;
                blue = value;
                break;
            case -1 :
            case 5:
            //default :
                red = value;
                green = p;
                blue = q;
                break;
            default :	 
                red = green = blue = 0;
                break;
        }
        
        // pack red, green and blue into 24-bit rgb
        int rgb = ((int) (red * 255)) << 16 | 
                ((int) (green * 255)) << 8 | 
                ((int) (blue * 255));
        
        return rgb;
    }
    public float[] toComponents(int red, int green, int blue, float components[]) {
        if (components == null || components.length != 3) {
            components = new float[3];
        }
        
        float r = red / 255f;
        float g = green / 255f;
        float b = blue / 255f;
        
        float max = Math.max(Math.max(r, g), b);
        float min = Math.min(Math.min(r, g), b);
        
        float hue;
        float saturation;
        float value;
        
        if (max == min) {
            hue = 0;
        } else if (max == r && g >= b) {
            hue = 60f * (g - b) / (max - min);
        } else if (max == r && g < b) {
            hue = 60f * (g - b) / (max - min) + 360f;
        } else if (max == g) {
            hue = 60f * (b - r) / (max - min) + 120f;
        } else /*if (max == b)*/ {
            hue = 60f * (r - g) / (max - min) + 240f;
        }
        
        value = max;
        
        if (max == 0) {
            saturation = 0;
        } else  {
            saturation = (max - min) / max;
        }
        
        components[0] = hue / 360f;
        components[1] = saturation;
        components[2] = value;
        
        return components;
    }

    public int getComponentCount() {
        return 3;
    }

}
