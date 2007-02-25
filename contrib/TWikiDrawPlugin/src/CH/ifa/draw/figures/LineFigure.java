/*
 * @(#)LineFigure.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import java.util.*;
import java.io.IOException;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.util.*;

/**
 * A line figure.
 */
public  class LineFigure extends PolyLineFigure {

    /*
     * Serialization support.
     */
    private static final long serialVersionUID = 511503575249212371L;
    private int lineFigureSerializedDataVersion = 1;

    /**
     * Constructs a LineFigure with both start and end set to Point(0,0).
     */
    public LineFigure() {
        addPoint(0, 0);
        addPoint(0, 0);
    }

    /**
     * Gets a copy of the start point.
     */
    public Point startPoint() {
        return pointAt(0);
    }

    /**
     * Gets a copy of the end point.
     */
    public Point endPoint() {
        return pointAt(1);
    }

    /**
     * Sets the start point.
     */
    public void  startPoint(int x, int y) {
        setPointAt(new Point(x,y), 0);
    }

    /**
     * Sets the end point.
     */
    public void  endPoint(int x, int y) {
        setPointAt(new Point(x,y), 1);
    }

    /**
     * Sets the start and end point.
     */
    public void setPoints(Point start, Point end) {
        setPointAt(start, 0);
        setPointAt(end, 1);
    }

    public void basicDisplayBox(Point origin, Point corner) {
        setPoints(origin, corner);
    }

}
