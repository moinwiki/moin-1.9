/*
 * @(#)DependencyFigure.java
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

package org.jhotdraw.samples.pert.figures;

import java.awt.*;
import java.awt.geom.Point2D;
import java.beans.*;
import static org.jhotdraw.draw.AttributeKeys.*;
import org.jhotdraw.draw.*;
import org.jhotdraw.xml.*;

/**
 * DependencyFigure.
 *
 * @author Werner Randelshofer.
 * @version $Id: DependencyFigure.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class DependencyFigure extends LineConnectionFigure {
    /** Creates a new instance. */
    public DependencyFigure() {
        STROKE_COLOR.basicSet(this, new Color(0x000099));
        STROKE_WIDTH.basicSet(this, 1d);
        END_DECORATION.basicSet(this, new ArrowTip());
        
        setAttributeEnabled(END_DECORATION, false);
        setAttributeEnabled(START_DECORATION, false);
        setAttributeEnabled(STROKE_DASHES, false);
        setAttributeEnabled(FONT_ITALIC, false);
        setAttributeEnabled(FONT_UNDERLINE, false);
    }
    
    /**
     * Checks if two figures can be connected. Implement this method
     * to constrain the allowed connections between figures.
     */
   @Override public boolean canConnect(Connector start, Connector end) {
        if ((start.getOwner() instanceof TaskFigure)
        && (end.getOwner() instanceof TaskFigure)) {
            
            TaskFigure sf = (TaskFigure) start.getOwner();
            TaskFigure ef = (TaskFigure) end.getOwner();
            
            // Disallow multiple connections to same dependent
            if (ef.getPredecessors().contains(sf)) {
                return false;
            }
            
            // Disallow cyclic connections
            return ! sf.isDependentOf(ef);
        }
        
        return false;
    }
    @Override public boolean canConnect(Connector start) {
        return (start.getOwner() instanceof TaskFigure);
    }
    

    /**
     * Handles the disconnection of a connection.
     * Override this method to handle this event.
     */
    @Override protected void handleDisconnect(Connector start, Connector end) {
        TaskFigure sf = (TaskFigure) start.getOwner();
        TaskFigure ef = (TaskFigure) end.getOwner();
        
        sf.removeDependency(this);
        ef.removeDependency(this);
    }
    
    /**
     * Handles the connection of a connection.
     * Override this method to handle this event.
     */
    @Override protected void handleConnect(Connector start, Connector end) {
        TaskFigure sf = (TaskFigure) start.getOwner();
        TaskFigure ef = (TaskFigure) end.getOwner();
        
        sf.addDependency(this);
        ef.addDependency(this);
    }
    
    public DependencyFigure clone() {
        DependencyFigure that = (DependencyFigure) super.clone();
        
        return that;
    }
    
    public int getLayer() {
        return 1;
    }
    
    @Override public void removeNotify(Drawing d) {
        if (getStartFigure() != null) {
            ((TaskFigure) getStartFigure()).removeDependency(this);
        }
        if (getEndFigure() != null) {
            ((TaskFigure) getEndFigure()).removeDependency(this);
        }
        super.removeNotify(d);
    }
}
