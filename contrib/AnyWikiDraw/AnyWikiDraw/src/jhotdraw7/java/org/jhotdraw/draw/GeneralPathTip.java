/*
 * @(#)GeneralPathLineDecoration.java
 *
 * Copyright (c) 1996-2006 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.draw;

import java.awt.geom.*;

/**
 * A {@link LineDecoration} which draws a general path.
 *
 * @author  Werner Randelshofer
 * @version $Id: GeneralPathTip.java 531 2009-06-13 10:20:39Z rawcoder $
 */
public class GeneralPathTip extends AbstractLineDecoration {
    private GeneralPath path;
    double decorationRadius;
    
    /** Creates a new instance. */
    public GeneralPathTip(GeneralPath path, double decorationRadius) {
        this(path, decorationRadius, false, true, false);
    }
    public GeneralPathTip(GeneralPath path, double decorationRadius, boolean isFilled, boolean isStroked, boolean isSolid) {
        super(isFilled, isStroked, isSolid);
        this.path = path;
        this.decorationRadius = decorationRadius;
    }
    
    protected GeneralPath getDecoratorPath(org.jhotdraw.draw.Figure f) {
        return (GeneralPath) path.clone();
    }
    
    protected double getDecoratorPathRadius(org.jhotdraw.draw.Figure f) {
        return decorationRadius;
    }
}
