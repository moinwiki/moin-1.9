/*
 * @(#)PathTool.java
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

package org.jhotdraw.samples.odg;

import javax.swing.undo.*;
import org.jhotdraw.samples.svg.figures.*;
import org.jhotdraw.draw.*;
import org.jhotdraw.util.*;
import org.jhotdraw.undo.*;
import java.awt.*;
import java.awt.geom.*;
import java.awt.event.*;
import java.util.*;
import org.jhotdraw.geom.*;
/**
 * Tool to scribble a ODGPath
 *
 * @author  Werner Randelshofer
 * @version $Id: PathTool.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class PathTool extends BezierTool {
    /**
     * Set this to true to turn on debugging output on System.out.
     */
    private final static boolean DEBUG = false;
    /**
     * The path prototype for new figures.
     */
    private SVGPathFigure pathPrototype;
    
    /** Creates a new instance. */
    public PathTool(SVGPathFigure pathPrototype, SVGBezierFigure bezierPrototype) {
        this(pathPrototype, bezierPrototype, null);
    }
    /** Creates a new instance. */
    public PathTool(SVGPathFigure pathPrototype, SVGBezierFigure bezierPrototype, Map<AttributeKey,Object> attributes) {
        super(bezierPrototype, attributes);
        this.pathPrototype = pathPrototype;
    }
    @SuppressWarnings("unchecked")
    protected SVGPathFigure createPath() {
        SVGPathFigure f = (SVGPathFigure) pathPrototype.clone();
        getEditor().applyDefaultAttributesTo(f);
        if (attributes != null) {
            for (Map.Entry<AttributeKey, Object> entry : attributes.entrySet()) {
                entry.getKey().basicSet(f, entry.getValue());
            }
        }
        return f;
    }
    @Override protected void finishCreation(BezierFigure createdFigure, DrawingView creationView) {
        if (DEBUG) System.out.println("PathTool.finishCreation "+createdFigure);
        creationView.getDrawing().remove(createdFigure);
        SVGPathFigure createdPath = createPath();
        createdPath.removeAllChildren();
        createdPath.add(createdFigure);
        creationView.getDrawing().add(createdPath);
        creationView.addToSelection(createdPath);
        fireUndoEvent(createdPath, creationView);
    }
}
