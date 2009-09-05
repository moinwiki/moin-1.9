/*
 * @(#)ArrowTip.java
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
import org.jhotdraw.xml.DOMInput;
import org.jhotdraw.xml.DOMOutput;
import org.jhotdraw.xml.DOMStorable;

/**
 * A {@link LineDecoration} which draws an arrow tip.
 *
 * @author Werner Randelshofer
 * @version $Id: ArrowTip.java 531 2009-06-13 10:20:39Z rawcoder $
 */
public class ArrowTip extends AbstractLineDecoration
implements DOMStorable {
    /**
     * Pointiness of arrow.
     */
    private double  angle;         
    private double  outerRadius;   
    private double  innerRadius;
    
    public ArrowTip() {
        this(0.35, 12, 11.3);
    }
    
    /**
     * Constructs an arrow tip with the specified angle and outer and inner 
     * radius.
     */
    public ArrowTip(double angle, double outerRadius, double innerRadius) {
        this(angle, outerRadius, innerRadius, true, false, true);
    }
    /**
     * Constructs an arrow tip with the specified parameters.
     */
    public ArrowTip(double angle, double outerRadius, double innerRadius, boolean isFilled, boolean isStroked, boolean isSolid) {
        super(isFilled, isStroked, isSolid);
        this.angle = angle;
        this.outerRadius = outerRadius;
        this.innerRadius = innerRadius;
    }
    
    
    protected GeneralPath getDecoratorPath(Figure f) {
        // FIXME - This should take the stroke join an the outer radius into
        // account to compute the offset properly.
        double offset = (isStroked()) ? 1 : 0;
        
        
        
        GeneralPath path = new GeneralPath();
        path.moveTo((float) (outerRadius * Math.sin(-angle)), (float) (offset + outerRadius * Math.cos(-angle)));
        path.lineTo(0, (float) offset);
        path.lineTo((float) (outerRadius * Math.sin(angle)), (float) (offset + outerRadius * Math.cos(angle)));
        if (innerRadius != 0) {
            path.lineTo(0, (float) (innerRadius + offset));
            path.closePath();
        }
        
        return path;
    }
    
    protected double getDecoratorPathRadius(Figure f) {
        double offset = (isStroked()) ? 0.5 : -0.1;

        return innerRadius + offset;
    }
    
    public void read(DOMInput in) {
        angle = in.getAttribute("angle", 0.35f);
        innerRadius = in.getAttribute("innerRadius", 12f);
        outerRadius = in.getAttribute("outerRadius", 12f);
        setFilled(in.getAttribute("isFilled", false));
        setStroked(in.getAttribute("isStroked", false));
        setSolid(in.getAttribute("isSolid", false));
    }
    
    public void write(DOMOutput out) {
        out.addAttribute("angle", angle);
        out.addAttribute("innerRadius", innerRadius);
        out.addAttribute("outerRadius", outerRadius);
        out.addAttribute("isFilled", isFilled());
        out.addAttribute("isStroked", isStroked());
        out.addAttribute("isSolid", isSolid());
    }
    
}
