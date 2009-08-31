/*
 * @(#)TranslationDirection.java
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

package org.jhotdraw.draw;

import java.awt.Point;
import java.awt.geom.Point2D;

/**
 * Specifies the possible directions for translations on a two-dimensional plane.
 * <p>
 * This enumeration is used by drawing tools and handles to perform constrained
 * transforms of figures on a drawing.
 * 
 * @see Constrainer
 *
 * @author Werner Randelshofer
 * @version $Id: TranslationDirection.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public enum TranslationDirection {
    NORTH,
    WEST,
    SOUTH,
    EAST,
    NORTH_WEST,
    SOUTH_WEST,
    NORTH_EAST,
    SOUTH_EAST;
    
    /**
     * Returns the direction from the provided start point to the end point.
     * Returns null, if both points are at the same location.
     */
    public static TranslationDirection getDirection(Point startPoint, Point endPoint) {
        int dx = endPoint.x - startPoint.x;
        int dy = endPoint.y - startPoint.y;
        
        if (dx == 0) {
            if (dy == 0) {
                return null;
            } else if (dy > 0) {
                return SOUTH;
            } else {
                return NORTH;
            }
        } else if (dx > 0) {
            if (dy == 0) {
                return EAST;
            } else if (dy > 0) {
                return SOUTH_EAST;
            } else {
                return NORTH_EAST;
            }
        } else {
            if (dy == 0) {
                return WEST;
            } else if (dy > 0) {
                return SOUTH_WEST;
            } else {
                return NORTH_WEST;
            }
        }
    }
    /**
     * Returns the direction from the provided start point to the end point.
     * Returns null, if both points are at the same location.
     */
    public static TranslationDirection getDirection(Point2D.Double startPoint, Point2D.Double endPoint) {
        double dx = endPoint.x - startPoint.x;
        double dy = endPoint.y - startPoint.y;
        
        if (dx == 0) {
            if (dy == 0) {
                return null;
            } else if (dy > 0) {
                return SOUTH;
            } else {
                return NORTH;
            }
        } else if (dx > 0) {
            if (dy == 0) {
                return EAST;
            } else if (dy > 0) {
                return SOUTH_EAST;
            } else {
                return NORTH_EAST;
            }
        } else {
            if (dy == 0) {
                return WEST;
            } else if (dy > 0) {
                return SOUTH_WEST;
            } else {
                return NORTH_WEST;
            }
        }
    }
}
