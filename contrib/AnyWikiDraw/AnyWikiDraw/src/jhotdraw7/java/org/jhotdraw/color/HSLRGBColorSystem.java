/*
 * @(#)HSLRGBColorSystem.java
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

import java.awt.*;
import javax.swing.*;

/**
 * A ColorSystem for HSL color components (hue, saturation, lightness) based
 * on the primary colors red, green and blue.
 *
 * @author  Werner Randelshofer
 * @version $Id: HSLRGBColorSystem.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class HSLRGBColorSystem extends AbstractColorSystem {

    /**
     * Creates a new instance.
     */
    public HSLRGBColorSystem() {
    }

    public int toRGB(float... components) {
        float hue = components[0];
        float saturation = components[1];
        float lightness = components[2];

        // compute p and q from saturation and lightness
        float q;
        if (lightness < 0.5f) {
            q = lightness * (1f + saturation);
        } else {
            q = lightness + saturation - (lightness * saturation);
        }
        float p = 2f * lightness - q;

        // normalize hue to -1..+1
        float hk = hue - (float) Math.floor(hue); // / 360f;

        // compute red, green and blue
        float red = hk + 1f / 3f;
        float green = hk;
        float blue = hk - 1f / 3f;

        // normalize rgb values
        if (red < 0) {
            red = red + 1f;
        } else if (red > 1) {
            red = red - 1f;
        }

        if (green < 0) {
            green = green + 1f;
        } else if (green > 1) {
            green = green - 1f;
        }

        if (blue < 0) {
            blue = blue + 1f;
        } else if (blue > 1) {
            blue = blue - 1f;
        }


        // adjust rgb values
        if (red < 1f / 6f) {
            red = p + ((q - p) * 6 * red);
        } else if (red < 0.5f) {
            red = q;
        } else if (red < 2f / 3f) {
            red = p + ((q - p) * 6 * (2f / 3f - red));
        } else {
            red = p;
        }
        
        if (green < 1f / 6f) {
            green = p + ((q - p) * 6 * green);
        } else if (green < 0.5f) {
            green = q;
        } else if (green < 2f / 3f) {
            green = p + ((q - p) * 6 * (2f / 3f - green));
        } else {
            green = p;
        }

        if (blue < 1f / 6f) {
            blue = p + ((q - p) * 6 * blue);
        } else if (blue < 0.5f) {
            blue = q;
        } else if (blue < 2f / 3f) {
            blue = p + ((q - p) * 6 * (2f / 3f - blue));
        } else {
            blue = p;
        }


        // pack red, green and blue into 24-bit rgb
        int rgb = ((int) (red * 255)) << 16 |
                ((int) (green * 255)) << 8 |
                ((int) (blue * 255));

        return rgb;
    }

    public float[] toComponents(int red, int green, int blue, float[] components) {
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
        float luminance;

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

        luminance = (max + min) / 2f;

        if (max == min) {
            saturation = 0;
        } else if (luminance <= 0.5f) {
            saturation = (max - min) / (max + min);
        } else /* if (lightness  > 0.5f)*/ {
            saturation = (max - min) / (2 - (max + min));
        }

        components[0] = hue / 360f;
        components[1] = saturation;
        components[2] = luminance;

        return components;
    }

    public int getComponentCount() {
        return 3;
    }

}
