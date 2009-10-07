/*
 * @(#)Gradient.java
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

package org.jhotdraw.samples.svg;

import java.awt.*;
import java.awt.geom.AffineTransform;
import org.jhotdraw.draw.*;

/**
 * Represents an SVG Gradient.
 *
 * @author Werner Randelshofer
 * @version $Id: Gradient.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public interface Gradient extends Cloneable {
    public Paint getPaint(Figure f, double opacity);
    public boolean isRelativeToFigureBounds();
    public void transform(AffineTransform tx);
    public Object clone();
    public void makeRelativeToFigureBounds(Figure f);
}
