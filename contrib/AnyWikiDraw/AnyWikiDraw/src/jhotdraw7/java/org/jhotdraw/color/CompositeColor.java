/**
 * @(#)CompositeColor.java
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

import java.awt.Color;

/**
 * CompositeColor represents an immutable value of a color system.
 *
 * @author Werner Randelshofer
 * @version $Id: CompositeColor.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class CompositeColor implements Cloneable {
    private ColorSystem system;
    private float[] components;
    private Color color;
    
    public CompositeColor(ColorSystem system, float... components) {
        this.system = system;
        this.components = components.clone();
    }
    public CompositeColor(ColorSystem system, Color color) {
        this.system = system;
        this.components = system.toComponents(color.getRGB(), null);
    }
    
    public float[] getComponents() {
        return components.clone();
    }
    
    public float getComponent(int i) {
        return components[i];
    }
    
    public float[] getComponents(float[] reuse) {
        if (reuse == null || reuse.length != system.getComponentCount()) {
            reuse = new float[system.getComponentCount()];
        }
        System.arraycopy(components, 0, reuse, 0, system.getComponentCount());
        return reuse;
    }
    
    public Color getColor() {
        if (color == null) {
            color = new Color(system.toRGB(components));
        }
        return color;
    }
    
    public ColorSystem getSystem() {
        return system;
    }
    
    public String toString() {
        StringBuffer buf = new StringBuffer();
        buf.append("CompositeColor[");
        for (int i=0; i < components.length; i++) {
            if (i != 0) { buf.append(','); }
            buf.append((int) (components[i] * 100));
        }
        buf.append("]");
        return buf.toString();
    }
    
    public CompositeColor clone() {
        try {
            CompositeColor that = (CompositeColor) super.clone();
            that.components = this.components.clone();
            return that;
        } catch (CloneNotSupportedException ex) {
            throw new InternalError("CompositeColor not cloneable.");
        }
    }
}
