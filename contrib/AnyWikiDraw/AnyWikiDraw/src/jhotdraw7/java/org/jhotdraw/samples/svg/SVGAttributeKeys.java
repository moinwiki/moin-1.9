/*
 * @(#)SVGAttributeKeys.java
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
import org.jhotdraw.draw.*;
import org.jhotdraw.util.ResourceBundleUtil;

/**
 * SVGAttributeKeys.
 *
 * @author Werner Randelshofer
 * @version $Id: SVGAttributeKeys.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class SVGAttributeKeys extends AttributeKeys {
     private final static ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.svg.Labels");
   
    public enum TextAnchor {
        START, MIDDLE, END
    }
    
    /**
     * Specifies the title of an SVG drawing.
     * This attribute can be null, to indicate that the drawing has no title.
     */
    public final static AttributeKey<String> TITLE = new AttributeKey<String>("title", String.class, null, true, labels);
    /**
     * Specifies the description of an SVG drawing.
     * This attribute can be null, to indicate that the drawing has no description.
     */
    public final static AttributeKey<String> DESCRIPTION = new AttributeKey<String>("description", String.class, null, true, labels);
    /**
     * Specifies the viewport-fill of an SVG viewport.
     * This attribute can be null, to indicate that the viewport has no viewport-fill.
     */
    public final static AttributeKey<Color> VIEWPORT_FILL = CANVAS_FILL_COLOR;
    /**
     * Specifies the viewport-fill-opacity of an SVG viewport.
     */
    public final static AttributeKey<Double> VIEWPORT_FILL_OPACITY = CANVAS_FILL_OPACITY;
    /**
     * Specifies the width of an SVG viewport.
     */
    public final static AttributeKey<Double> VIEWPORT_WIDTH = CANVAS_WIDTH;
    /**
     * Specifies the height of an SVG viewport.
     */
    public final static AttributeKey<Double> VIEWPORT_HEIGHT = CANVAS_HEIGHT;
    
    
    /**
     * Specifies the text anchor of a SVGText figure.
     */
    public final static AttributeKey<TextAnchor> TEXT_ANCHOR = new AttributeKey<TextAnchor>("textAnchor", TextAnchor.class, TextAnchor.START, false, labels);
    
    public enum TextAlign {
        START, CENTER, END
    }
    /**
     * Specifies the text alignment of a SVGText figure.
     */
    public final static AttributeKey<TextAlign> TEXT_ALIGN = new AttributeKey<TextAlign>("textAlign",TextAlign.class,TextAlign.START, false, labels);
    /**
     * Specifies the fill gradient of a SVG figure.
     */
    public final static AttributeKey<Gradient> FILL_GRADIENT = new AttributeKey<Gradient>("fillGradient",Gradient.class, null, true, labels);
    
    /**
     * Specifies the fill opacity of a SVG figure.
     * This is a value between 0 and 1 whereas 0 is translucent and 1 is fully opaque.
     */
    public final static AttributeKey<Double> FILL_OPACITY = new AttributeKey<Double>("fillOpacity", Double.class, 1d, false, labels);
    /**
     * Specifies the overall opacity of a SVG figure.
     * This is a value between 0 and 1 whereas 0 is translucent and 1 is fully opaque.
     */
    public final static AttributeKey<Double> OPACITY = new AttributeKey<Double>("opacity",Double.class, 1d, false, labels);
    
    
    /**
     * Specifies the stroke gradient of a SVG figure.
     */
    public final static AttributeKey<Gradient> STROKE_GRADIENT = new AttributeKey<Gradient>("strokeGradient", Gradient.class, null, true, labels);
    /**
     * Specifies the stroke opacity of a SVG figure.
     * This is a value between 0 and 1 whereas 0 is translucent and 1 is fully opaque.
     */
    public final static AttributeKey<Double> STROKE_OPACITY = new AttributeKey<Double>("strokeOpacity",Double.class, 1d, false, labels);
    
    /**
     * Specifies a link.
     * In an SVG file, the link is stored in a "a" element which encloses the
     * figure.
     * http://www.w3.org/TR/SVGMobile12/linking.html#AElement
     */
    public final static AttributeKey<String> LINK = new AttributeKey<String>("link",String.class, null, true, labels);
    /**
     * Specifies a link target.
     * In an SVG file, the link is stored in a "a" element which encloses the
     * figure.
     * http://www.w3.org/TR/SVGMobile12/linking.html#AElement
     */
    public final static AttributeKey<String> LINK_TARGET = new AttributeKey<String>("linkTarget", String.class,null, true, labels);
    
    
    /**
     * Gets the fill paint for the specified figure based on the attributes
     * FILL_GRADIENT, FILL_OPACITY, FILL_PAINT and the bounds of the figure.
     * Returns null if the figure is not filled.
     */
    public static Paint getFillPaint(Figure f) {
        double opacity = FILL_OPACITY.get(f);
        if (FILL_GRADIENT.get(f) != null) {
            return FILL_GRADIENT.get(f).getPaint(f, opacity);
        }
        Color color = FILL_COLOR.get(f);
        if (color != null) {
            if (opacity != 1) {
                color = new Color(
                        (color.getRGB() & 0xffffff) | (int) (opacity * 255) << 24,
                        true);
            }
        }
        return color;
    }
    /**
     * Gets the stroke paint for the specified figure based on the attributes
     * STROKE_GRADIENT, STROKE_OPACITY, STROKE_PAINT and the bounds of the figure.
     * Returns null if the figure is not filled.
     */
    public static Paint getStrokePaint(Figure f) {
        double opacity = STROKE_OPACITY.get(f);
        if (STROKE_GRADIENT.get(f) != null) {
            return STROKE_GRADIENT.get(f).getPaint(f, opacity);
        }
        Color color = STROKE_COLOR.get(f);
        if (color != null) {
            if (opacity != 1) {
                color = new Color(
                        (color.getRGB() & 0xffffff) | (int) (opacity * 255) << 24,
                        true);
            }
        }
        return color;
    }
    
    
    /** Sets SVG default values. */
    public static void setDefaults(Figure f) {
        // Fill properties
        // http://www.w3.org/TR/SVGMobile12/painting.html#FillProperties
        FILL_COLOR.basicSet(f, Color.black);
        WINDING_RULE.basicSet(f, WindingRule.NON_ZERO);
        
        // Stroke properties
        // http://www.w3.org/TR/SVGMobile12/painting.html#StrokeProperties
        STROKE_COLOR.basicSet(f, null);
        STROKE_WIDTH.basicSet(f, 1d);
        STROKE_CAP.basicSet(f, BasicStroke.CAP_BUTT);
        STROKE_JOIN.basicSet(f, BasicStroke.JOIN_MITER);
        STROKE_MITER_LIMIT.basicSet(f, 4d);
        IS_STROKE_MITER_LIMIT_FACTOR.basicSet(f, false);
        STROKE_DASHES.basicSet(f, null);
        STROKE_DASH_PHASE.basicSet(f, 0d);
        IS_STROKE_DASH_FACTOR.basicSet(f, false);
    }
    /**
     * Returns the distance, that a Rectangle needs to grow (or shrink) to
     * make hit detections on a shape as specified by the FILL_UNDER_STROKE and STROKE_POSITION
     * attributes of a figure.
     * The value returned is the number of units that need to be grown (or shrunk)
     * perpendicular to a stroke on an outline of the shape.
     */
    public static double getPerpendicularHitGrowth(Figure f) {
        double grow;
        if (STROKE_COLOR.get(f) == null && STROKE_GRADIENT.get(f) == null) {
            grow = getPerpendicularFillGrowth(f);
        } else {
            double strokeWidth = AttributeKeys.getStrokeTotalWidth(f);
            grow = getPerpendicularDrawGrowth(f) + strokeWidth / 2d;
        }
        return grow;
    }
}
