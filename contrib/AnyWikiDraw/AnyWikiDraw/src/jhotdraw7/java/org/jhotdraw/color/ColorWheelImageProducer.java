/*
 * @(#)ColorWheelImageProducer.java
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
import java.awt.image.*;

/**
 * Produces the image of a ColorWheel.
 *
 * @see JColorWheel
 *
 * @author  Werner Randelshofer
 * @version $Id: ColorWheelImageProducer.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ColorWheelImageProducer extends MemoryImageSource {

    protected int[] pixels;
    protected int w,  h;
    protected float verticalValue = 1f;
    protected boolean isLookupValid = false;
    protected boolean isPixelsValid = false;
    /** Lookup table for angular component values. */
    protected float[] angulars;
    /** Lookup table for radial component values. */
    protected float[] radials;
    /** Lookup table for alphas. 
     * The alpha value is used for antialiasing the
     * color wheel.
     */
    protected int[] alphas;
    protected ColorSystem colorSystem;
    protected int radialIndex = 1;
    protected int angularIndex = 0;
    protected int verticalIndex = 2;

    /** Creates a new instance. */
    public ColorWheelImageProducer(ColorSystem sys, int w, int h) {
        super(w, h, null, 0, w);
        pixels = new int[w * h];
        this.w = w;
        this.h = h;
        this.colorSystem = sys;
        setAnimated(true);
        
        newPixels(pixels, ColorModel.getRGBdefault(), 0, w);
    }

    public int getRadius() {
        return Math.min(w, h) / 2 - 2;
    }
    
    public void setRadialComponentIndex(int newValue) {
        radialIndex = newValue;
        isPixelsValid = false;
    }
    public void setAngularComponentIndex(int newValue) {
        angularIndex = newValue;
        isPixelsValid = false;
    }
    public void setVerticalComponentIndex(int newValue) {
        verticalIndex = newValue;
        isPixelsValid = false;
    }

    protected void generateLookupTables() {
        radials = new float[w * h];
        angulars = new float[w * h];
        alphas = new int[w * h];
        float radius = getRadius();

        // blend is used to create a linear alpha gradient of two extra pixels
        float blend = (radius + 2f) / radius - 1f;

        // Center of the color wheel circle
        int cx = w / 2;
        int cy = h / 2;

        for (int x = 0; x < w; x++) {
            int kx = x - cx; // Kartesian coordinates of x
            int squarekx = kx * kx; // Square of kartesian x

            for (int y = 0; y < h; y++) {
                int ky = cy - y; // Kartesian coordinates of y

                int index = x + y * w;
                radials[index] = (float) Math.sqrt(squarekx + ky * ky) / radius;
                if (radials[index] <= 1f) {
                    alphas[index] = 0xff000000;
                } else {
                    alphas[index] = (int) ((blend - Math.min(blend, radials[index] - 1f)) * 255 / blend) << 24;
                    radials[index] = 1f;
                }
                if (alphas[index] != 0) {
                    angulars[index] = (float) (Math.atan2(ky, kx) / Math.PI / 2d);
                }
            }
        }
        isLookupValid = true;
    }

    public void setVerticalValue(float newValue) {
        isPixelsValid = isPixelsValid && verticalValue == newValue;
        verticalValue = newValue;
    }

    public boolean needsGeneration() {
        return ! isPixelsValid;
    }

    public void regenerateColorWheel() {
        if (! isPixelsValid) {
            generateColorWheel();
        }
    }

    public void generateColorWheel() {
        if (! isLookupValid) {
            generateLookupTables();
        }
        
        float[] components = new float[colorSystem.getComponentCount()];
        float radius = (float) Math.min(w, h);
        for (int index = 0; index < pixels.length; index++) {
            if (alphas[index] != 0) {
                components[angularIndex] = angulars[index];
                components[radialIndex] = radials[index];
                components[verticalIndex] = verticalValue;
                pixels[index] = alphas[index] | 0xffffff & colorSystem.toRGB(components);
            }
        }
        newPixels();
        isPixelsValid = true;
    }

    protected Point getColorLocation(Color c, int width, int height) {
        float[] hsb = new float[3];
        hsb = colorSystem.toComponents(c.getRGB(), hsb);
        return getColorLocation(hsb[0], hsb[1], hsb[2], width, height);
    }

    protected Point getColorLocation(float hue, float saturation, float brightness, int width, int height) {
        float radial, angular;
        switch (angularIndex) {
            case 0 : default : angular = hue; break;
            case 1 : angular = saturation; break;
            case 2 : angular = brightness; break;
        }
        switch (radialIndex) {
            case 0 : default : radial = hue; break;
            case 1 : radial = saturation; break;
            case 2 : radial = brightness; break;
        }
        
        
        float radius = Math.min(width, height) / 2f;
        radial = Math.max(0f, Math.min(1f, radial));
        Point p = new Point(
                width / 2 + (int) (radius * radial * Math.cos(angular * Math.PI * 2d)),
                height / 2 - (int) (radius * radial * Math.sin(angular * Math.PI * 2d)));
        return p;
    }

    protected Point getColorLocation(CompositeColor c, int width, int height) {
        return getColorLocation(c.getComponents(), width, height);
    }

    protected Point getColorLocation(float[] components, int width, int height) {
        return getColorLocation(components[0], components[1], components[2], width, height);
    }

    protected float[] getColorAt(int x, int y, int width, int height) {
        x -= width / 2;
        y -= height / 2;
        float r = (float) Math.sqrt(x * x + y * y);
        float theta = (float) Math.atan2(y, -x);

        float angular = (float) (0.5 + (theta / Math.PI / 2d));

        float[] hsb = new float[3];
        hsb[angularIndex] = angular;
        hsb[radialIndex] = Math.min(1f, (float) r / getRadius());
        hsb[verticalIndex] = verticalValue;
        return hsb;
    }
}
