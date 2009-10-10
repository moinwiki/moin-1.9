/*
 * @(#)LinearGradient.java
 *
 * Copyright (c) 1996-2009 by the original authors of JHotDraw
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
import java.awt.geom.*;
import java.util.Arrays;
import org.jhotdraw.draw.*;
import static org.jhotdraw.samples.svg.SVGAttributeKeys.*;

/**
 * Represents an SVG LinearGradient.
 *
 * @author Werner Randelshofer
 * @version $Id: LinearGradient.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class LinearGradient implements Gradient {
    private double x1;
    private double y1;
    private double x2;
    private double y2;
    private boolean isRelativeToFigureBounds = true;
    private double[] stopOffsets;
    private Color[] stopColors;
    private double[] stopOpacities;
    private AffineTransform transform;
    private int spreadMethod;
    
    /** Creates a new instance. */
    public LinearGradient() {
    }
    public LinearGradient(
            double x1, double y1, double x2, double y2,
            double[] stopOffsets, Color[] stopColors, double[] stopOpacities,
            boolean isRelativeToFigureBounds,
            AffineTransform tx) {
        this.x1 = x1;
        this.y1 = y1;
        this.x2 = x2;
        this.y2 = y2;
        this.stopOffsets = stopOffsets;
        this.stopColors = stopColors;
        this.stopOpacities = stopOpacities;
        this.isRelativeToFigureBounds = isRelativeToFigureBounds;
        this.transform = tx;
    }
    public void setGradientVector(double x1, double y1, double x2, double y2) {
        this.x1 = x1;
        this.y1 = y1;
        this.x2 = x2;
        this.y2 = y2;
    }
    public void setStops(double[] offsets, Color[] colors, double[] stopOpacities) {
        this.stopOffsets = offsets;
        this.stopColors = colors;
        this.stopOpacities = stopOpacities;
    }
    public void setRelativeToFigureBounds(boolean b) {
        isRelativeToFigureBounds = b;
    }
    public boolean isRelativeToFigureBounds() {
        return isRelativeToFigureBounds;
    }
    
    public double getX1() {
        return x1;
    }
    public double getY1() {
        return y1;
    }
    public double getX2() {
        return x2;
    }
    public double getY2() {
        return y2;
    }
    public double[] getStopOffsets() {
        return stopOffsets.clone();
    }
    public Color[] getStopColors() {
        return stopColors.clone();
    }
    public double[] getStopOpacities() {
        return stopOpacities.clone();
    }
    public AffineTransform getTransform() {
        return transform;
    }
    
    public Paint getPaint(Figure f, double opacity) {
        // No stops, like fill = none
        if (stopColors.length == 0) {
            return new Color(0x0,true);
        }
        
        // Compute colors and fractions for the paint
        Color[] colors = new Color[stopColors.length];
        float[] fractions = new float[stopColors.length];
        float previousFraction = 0;
        for (int i=0; i < stopColors.length; i++) {
            // Each fraction must be larger or equal the previous fraction.
            fractions[i] = Math.min(1f, Math.max(previousFraction, (float) stopOffsets[i]));
            colors[i] = new Color(
                    (stopColors[i].getRGB() & 0xffffff) |
                    ((int) (opacity * stopOpacities[i] * 255) << 24),
                    true
                    );
            previousFraction = fractions[i];
        }
        
        
        // Compute the dimensions and transforms for the paint
        Point2D.Double p1;
        Point2D.Double p2;
        p1 = new Point2D.Double(x1, y1);
        p2 = new Point2D.Double(x2, y2);
        AffineTransform t = transform;
        if (isRelativeToFigureBounds) {
            t = (AffineTransform) t.clone();
            Rectangle2D.Double bounds = f.getBounds();
            t.translate(bounds.x, bounds.y);
            t.scale(bounds.width, bounds.height);
        }
        
        // Construct a solid color, if only one stop color is given, or if
        // transform is not invertible
        if (stopColors.length == 1 || t.getDeterminant() == 0) {
            return colors[0];
        }
        // Construct a gradient
        org.apache.batik.ext.awt.LinearGradientPaint gp;
        gp = new org.apache.batik.ext.awt.LinearGradientPaint(
                p1, p2, fractions, colors,
                org.apache.batik.ext.awt.LinearGradientPaint.NO_CYCLE,
                org.apache.batik.ext.awt.LinearGradientPaint.SRGB,
                t
                );
        
        return gp;
    }
    
    @Override
    public String toString() {
        StringBuilder buf = new StringBuilder();
        buf.append("LinearGradient@");
        buf.append(hashCode());
        buf.append('(');
        for (int i=0; i < stopOffsets.length; i++) {
            if (i != 0) buf.append(',');
            buf.append(stopOffsets[i]);
            buf.append('=');
            buf.append(stopOpacities[i]);
            buf.append(' ');
            buf.append(Integer.toHexString(stopColors[i].getRGB()));
        }
        buf.append(')');
        return buf.toString();
    }
    
    public void setTransform(AffineTransform tx) {
        transform = tx;
    }
    
    public void transform(AffineTransform tx) {
        if (transform == null) {
            transform = (AffineTransform) tx.clone();
        } else {
            transform.preConcatenate(tx);
        }
    }
    public Object clone() {
        try {
            LinearGradient that = (LinearGradient) super.clone();
            that.stopOffsets = this.stopOffsets.clone();
            that.stopColors = this.stopColors.clone();
            that.stopOpacities = this.stopOpacities.clone();
            that.transform = (AffineTransform) this.transform.clone();
            return that;
        } catch (CloneNotSupportedException ex) {
            InternalError e = new InternalError();
            e.initCause(ex);
            throw e;
        }
    }
    
    public void makeRelativeToFigureBounds(Figure f) {
        if (! isRelativeToFigureBounds) {
            isRelativeToFigureBounds = true;
            Rectangle2D.Double bounds = f.getBounds();
            x1 = (x1 - bounds.x) / bounds.width;
            y1 = (y1 - bounds.y) / bounds.height;
            x2 = (x2 - bounds.x) / bounds.width;
            y2 = (y2 - bounds.y) / bounds.height;
        }
    }
    
    public int hashCode() {
	long bits = Double.doubleToLongBits(x1);
	bits += Double.doubleToLongBits(y1) * 31;
	bits += Double.doubleToLongBits(x2) * 35;
	bits += Double.doubleToLongBits(y2) * 39;
	bits += stopColors[0].hashCode() * 43;
	bits += stopColors[stopColors.length - 1].hashCode() * 47;
	return (((int) bits) ^ ((int) (bits >> 32)));
    }
    
    public boolean equals(Object o) {
        if (o instanceof LinearGradient) {
            return equals((LinearGradient) o);
        } else {
            return false;
        }
    }
    public boolean equals(LinearGradient that) {
        return x1 == that.x1 &&
                y1 == that.y1 &&
                x2 == that.x2 &&
                y2 == that.y2 &&
                isRelativeToFigureBounds == that.isRelativeToFigureBounds &&
                Arrays.equals(stopOffsets, that.stopOffsets) &&
                Arrays.equals(stopOpacities, that.stopOpacities) &&
                Arrays.equals(stopColors, that.stopColors) &&
                transform.equals(that.transform);
    }
}
