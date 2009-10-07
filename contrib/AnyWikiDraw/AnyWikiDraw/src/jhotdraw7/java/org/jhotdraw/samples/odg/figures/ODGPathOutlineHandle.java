/*
 * @(#)ODGPathOutlineHandle.java
 *
 * Copyright (c) 2007 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.samples.odg.figures;

import org.jhotdraw.draw.*;
import java.awt.*;
import static org.jhotdraw.samples.odg.ODGAttributeKeys.*;

/**
 * A non-interactive {@link Handle} which draws the outline of a
 * {@link ODGPathFigure} to make adjustments easier.
 * 
 * @author Werner Randelshofer
 * @version $Id: ODGPathOutlineHandle.java 532 2009-06-13 11:28:36Z rawcoder $
 */
public class ODGPathOutlineHandle extends AbstractHandle {
    private final static Color HANDLE_FILL_COLOR = new Color(0x00a8ff);
    private final static Color HANDLE_STROKE_COLOR = Color.WHITE;
    
    /** Creates a new instance. */
    public ODGPathOutlineHandle(ODGPathFigure owner) {
        super(owner);
    }
    
    public ODGPathFigure getOwner() {
        return (ODGPathFigure) super.getOwner();
    }
    
    protected Rectangle basicGetBounds() {
        return view.drawingToView(getOwner().getDrawingArea());
    }
    @Override public boolean contains(Point p) {
        return false;
    }
    
    public void trackStart(Point anchor, int modifiersEx) {
    }
    
    public void trackStep(Point anchor, Point lead, int modifiersEx) {
    }
    
    public void trackEnd(Point anchor, Point lead, int modifiersEx) {
    }
    
    @Override public void draw(Graphics2D g) {
        Shape bounds = getOwner().getPath();
        if (TRANSFORM.get(getOwner()) != null) {
            bounds = TRANSFORM.get(getOwner()).createTransformedShape(bounds);
        }
        bounds = view.getDrawingToViewTransform().createTransformedShape(bounds);
        g.setColor(HANDLE_FILL_COLOR);
        g.draw(bounds);
    }
}
