/*
 * @(#)CMYKICCColorSystem.java
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

import java.awt.color.*;
import java.io.*;

/**
 * A ColorSystem for CMYK color components (cyan, magenta, yellow, black) in
 * a color space defined by a ICC color profile (International Color Consortium).
 * <p>
 * XXX - This does not work. I think this is because of 
 * Java bug #4760025 at
 * http://bugs.sun.com/bugdatabase/view_bug.do?bug_id=4760025
 * but maybe I am doing something in the wrong way.
 * 
 *
 * @author  Werner Randelshofer
 * @version $Id: CMYKICCColorSystem.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class CMYKICCColorSystem extends AbstractColorSystem {

    private ICC_ColorSpace colorSpace;

    /**
     * Creates a new instance.
     */
    public CMYKICCColorSystem() {
        try {
            read(getClass().getResourceAsStream("Generic CMYK Profile.icc"));
        } catch (IOException e) {
            InternalError err = new InternalError("Couldn't load \"Generic CMYK Profile.icc\".");
            err.initCause(e);
            throw err;
        }

    }

    /**
     * Creates a new instance.
     */
    public CMYKICCColorSystem(InputStream iccProfile) throws IOException {
        read(iccProfile);
    }

    public void read(InputStream iccProfile) throws IOException {
        this.colorSpace = new ICC_ColorSpace(ICC_Profile.getInstance(iccProfile));
    }

    public float[] toComponents(int r, int g, int b, float[] component) {
        if (component == null || component.length != 4) {
            component = new float[4];
        }
        component[0] = r / 255f;
        component[1] = g / 255f;
        component[2] = b / 255f;
        float[] cmyk = colorSpace.fromRGB(component);
        System.arraycopy(cmyk, 0, component, 0, 4);
        return component;
    }

    public int toRGB(float... component) {
        float[] rgb = colorSpace.toRGB(component);
        return 0xff000000 | ((int) (rgb[0] * 255f) << 16) | ((int) (rgb[1] * 255f) << 8) | (int) (rgb[2] * 255f);
    }

    public int getComponentCount() {
        return 4;
    }

}
