/*
 * @(#)GridConstrainer.java
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
package org.jhotdraw.draw;

import java.awt.*;
import java.awt.geom.*;

/**
 * Constrains a point such that it falls on a grid.
 *
 * @author  Werner Randelshofer
 * @version $Id: GridConstrainer.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class GridConstrainer extends AbstractConstrainer {

    /**
     * The width of a minor grid cell.
     * The value 0 turns the constrainer off for the horizontal axis.
     */
    private double width;
    /**
     * The height of a minor grid cell.
     * The value 0 turns the constrainer off for the vertical axis.
     */
    private double height;
    
    /**
     * The theta for constrained rotations on the grid.  
     * The value 0 turns the constrainer off for rotations.
     */
    private double theta;
    /**
     * If this variable is true, the grid is drawn.
     * Note: Grid cells are only drawn, if they are at least two pixels apart
     * on the view coordinate system.
     */
    private boolean isVisible;
    /**
     * The color for minor grid cells.
     */
    private static Color minorColor = new Color(0xebebeb);
    /**
     * The color for major grid cells.
     */
    private static Color majorColor = new Color(0xcacaca);
    /**
     * The spacing factor for a major grid cell.
     */
    private int majorGridSpacing = 5;

    /**
     * Creates a new instance with a grid of 1x1.
     */
    public GridConstrainer() {
        this(1d, 1d, 0d, false);
    }

    /**
     * Creates a new instance with the specified grid size, 
     * and by 11.25° (in degrees) for rotations.
     * The grid is visible.
     *
     * @param width The width of a grid cell.
     * @param height The height of a grid cell.
     */
    public GridConstrainer(double width, double height) {
        this(width, height, Math.PI / 8d, true);
    }

    /**
     * Creates a new instance with the specified grid size.
     * and by 11.25° (in degrees) for rotations.
     *
     * @param width The width of a grid cell.
     * @param height The height of a grid cell.
     * @param visible Wether the grid is visible or not.
     */
    public GridConstrainer(double width, double height, boolean visible) {
        this(width, height, Math.PI / 8d, visible);
    }
    /**
     * Creates a new instance with the specified grid size.
     *
     * @param width The width of a grid cell.
     * @param height The height of a grid cell.
     * @param theta The theta for rotations in radians.
     * @param visible Wether the grid is visible or not.
     */
    public GridConstrainer(double width, double height, double theta, boolean visible) {
        if (width <= 0 || height <= 0) {
            throw new IllegalArgumentException("Width or height is <= 0");
        }
        this.width = width;
        this.height = height;
        this.theta = theta;
        this.isVisible = visible;
    }

    public double getWidth() {
        return width;
    }

    public double getHeight() {
        return height;
    }

    public double getTheta() {
        return theta;
    }

    public void setWidth(double newValue) {
        double oldValue = width;
        width = newValue;
        firePropertyChange("width", oldValue, newValue);
        fireStateChanged();
    }

    public void setHeight(double newValue) {
        double oldValue = height;
        height = newValue;
        firePropertyChange("height", oldValue, newValue);
        fireStateChanged();
    }

    public void setTheta(double newValue) {
        double oldValue = theta;
        theta = newValue;
        firePropertyChange("theta", oldValue, newValue);
        fireStateChanged();
    }

    /**
     * Constrains a point to the closest grid point in any direction.
     */
    public Point2D.Double constrainPoint(Point2D.Double p) {
        p.x = Math.round(p.x / width) * width;
        p.y = Math.round(p.y / height) * height;
        return p;
    }

    /**
     * Constrains the placement of a point towards a direction.
     * <p>
     * This method changes the point which is passed as a parameter.
     *
     * @param p A point on the drawing.
     * @param dir A direction.
     * @return Returns the constrained point.
     */
    protected Point2D.Double constrainPoint(Point2D.Double p, TranslationDirection dir) {
        Point2D.Double p0 = constrainPoint((Point2D.Double) p.clone());

        switch (dir) {
            case NORTH:
            case NORTH_WEST:
            case NORTH_EAST:
                if (p0.y < p.y) {
                    p.y = p0.y;
                } else if (p0.y > p.y) {
                    p.y = p0.y - height;
                }
                break;
            case SOUTH:
            case SOUTH_WEST:
            case SOUTH_EAST:
                if (p0.y < p.y) {
                    p.y = p0.y + height;
                } else if (p0.y > p.y) {
                    p.y = p0.y;
                }
                break;
        }
        switch (dir) {
            case WEST:
            case NORTH_WEST:
            case SOUTH_WEST:
                if (p0.x < p.x) {
                    p.x = p0.x;
                } else if (p0.x > p.x) {
                    p.x = p0.x - width;
                }
                break;
            case EAST:
            case NORTH_EAST:
            case SOUTH_EAST:
                if (p0.x < p.x) {
                    p.x = p0.x + width;
                } else if (p0.x > p.x) {
                    p.x = p0.x;
                }
                break;
        }

        return p;
    }

    /**
     * Moves a point to the closest grid point in a direction.
     */
    public Point2D.Double translatePoint(Point2D.Double p, TranslationDirection dir) {
        Point2D.Double p0 = constrainPoint((Point2D.Double) p.clone());

        switch (dir) {
            case NORTH:
            case NORTH_WEST:
            case NORTH_EAST:
                p.y = p0.y - height;
                break;
            case SOUTH:
            case SOUTH_WEST:
            case SOUTH_EAST:
                p.y = p0.y + height;
                break;
        }
        switch (dir) {
            case WEST:
            case NORTH_WEST:
            case SOUTH_WEST:
                p.x = p0.x - width;
                break;
            case EAST:
            case NORTH_EAST:
            case SOUTH_EAST:
                p.x = p0.x + width;
                break;
        }

        return p;
    }

    public Rectangle2D.Double constrainRectangle(Rectangle2D.Double r) {
        Point2D.Double p0 = constrainPoint(new Point2D.Double(r.x, r.y));
        Point2D.Double p1 = constrainPoint(new Point2D.Double(r.x + r.width, r.y + r.height));

        if (Math.abs(p0.x - r.x) < Math.abs(p1.x - r.x - r.width)) {
            r.x = p0.x;
        } else {
            r.x = p1.x - r.width;
        }
        if (Math.abs(p0.y - r.y) < Math.abs(p1.y - r.y - r.height)) {
            r.y = p0.y;
        } else {
            r.y = p1.y - r.height;
        }

        return r;
    }

    /**
     * Constrains the placement of a rectangle towards a direction.
     * <p>
     * This method changes the location of the rectangle which is passed as a
     * parameter. This method does not change the size of the rectangle.
     *
     * @param r A rectangle on the drawing.
     * @param dir A direction.
     * @return Returns the constrained rectangle.
     */
    protected Rectangle2D.Double constrainRectangle(Rectangle2D.Double r, TranslationDirection dir) {
        Point2D.Double p0 = new Point2D.Double(r.x, r.y);

        switch (dir) {
            case NORTH:
            case NORTH_WEST:
            case WEST:
                constrainPoint(p0, dir);
                break;
            case EAST:
            case NORTH_EAST:
                p0.x += r.width;
                constrainPoint(p0, dir);
                p0.x -= r.width;
                break;
            case SOUTH:
            case SOUTH_WEST:
                p0.y += r.height;
                constrainPoint(p0, dir);
                p0.y -= r.height;
                break;
            case SOUTH_EAST:
                p0.y += r.height;
                p0.x += r.width;
                constrainPoint(p0, dir);
                p0.y -= r.height;
                p0.x -= r.width;
                break;
        }

        r.x = p0.x;
        r.y = p0.y;

        return r;
    }

    public Rectangle2D.Double translateRectangle(Rectangle2D.Double r, TranslationDirection dir) {
        double x = r.x;
        double y = r.y;

        constrainRectangle(r, dir);

        switch (dir) {
            case NORTH:
            case NORTH_WEST:
            case NORTH_EAST:
                if (y == r.y) {
                    r.y -= height;
                }
                break;
            case SOUTH:
            case SOUTH_WEST:
            case SOUTH_EAST:
                if (y == r.y) {
                    r.y += height;
                }
                break;
        }
        switch (dir) {
            case WEST:
            case NORTH_WEST:
            case SOUTH_WEST:
                if (x == r.x) {
                    r.x -= width;
                }
                break;
            case EAST:
            case NORTH_EAST:
            case SOUTH_EAST:
                if (x == r.x) {
                    r.x += width;
                }
                break;
        }

        return r;
    }

    public String toString() {
        return super.toString() + "[" + width + "," + height + "]";
    }

    public boolean isVisible() {
        return isVisible;
    }

    public void setVisible(boolean newValue) {
        boolean oldValue = isVisible;
        isVisible = newValue;
        firePropertyChange("visible", oldValue, newValue);
        fireStateChanged();
    }

    /**
     * Spacing between major grid lines.
     */
    public int getMajorGridSpacing() {
        return majorGridSpacing;
    }

    /**
     * Spacing between major grid lines.
     */
    public void setMajorGridSpacing(int newValue) {
        int oldValue = majorGridSpacing;
        majorGridSpacing = newValue;
        firePropertyChange("majorGridSpacing", oldValue, newValue);
        fireStateChanged();
    }

    public void draw(Graphics2D g, DrawingView view) {
        if (isVisible) {
            AffineTransform t = view.getDrawingToViewTransform();
            Rectangle viewBounds = g.getClipBounds();
            Rectangle2D.Double bounds = view.viewToDrawing(viewBounds);

            Point2D.Double origin = constrainPoint(new Point2D.Double(bounds.x, bounds.y));
            Point2D.Double point = new Point2D.Double();
            Point2D.Double viewPoint = new Point2D.Double();

            // vertical grid lines are only drawn, if they are at least two 
            // pixels apart on the view coordinate system.
            if (width * view.getScaleFactor() > 2) {
                g.setColor(minorColor);
                for (int i = (int) (origin.x / width),  m = (int) ((origin.x + bounds.width) / width) + 1; i <= m; i++) {
                    g.setColor((i % majorGridSpacing == 0) ? majorColor : minorColor);

                    point.x = width * i;
                    t.transform(point, viewPoint);
                    g.drawLine((int) viewPoint.x, (int) viewBounds.y,
                            (int) viewPoint.x, (int) (viewBounds.y + viewBounds.height));
                }
            } else if (width * majorGridSpacing * view.getScaleFactor() > 2) {
                g.setColor(majorColor);
                for (int i = (int) (origin.x / width),  m = (int) ((origin.x + bounds.width) / width) + 1; i <= m; i++) {
                    if (i % majorGridSpacing == 0) {
                        point.x = width * i;
                        t.transform(point, viewPoint);
                        g.drawLine((int) viewPoint.x, (int) viewBounds.y,
                                (int) viewPoint.x, (int) (viewBounds.y + viewBounds.height));
                    }
                }
            }

            // horizontal grid lines are only drawn, if they are at least two 
            // pixels apart on the view coordinate system.
            if (height * view.getScaleFactor() > 2) {
                g.setColor(minorColor);
                for (int i = (int) (origin.y / height),  m = (int) ((origin.y + bounds.height) / height) + 1; i <= m; i++) {
                    g.setColor((i % majorGridSpacing == 0) ? majorColor : minorColor);

                    point.y = height * i;
                    t.transform(point, viewPoint);
                    g.drawLine((int) viewBounds.x, (int) viewPoint.y,
                            (int) (viewBounds.x + viewBounds.width), (int) viewPoint.y);
                }
            } else if (height * majorGridSpacing * view.getScaleFactor() > 2) {
                g.setColor(majorColor);
                for (int i = (int) (origin.y / height),  m = (int) ((origin.y + bounds.height) / height) + 1; i <= m; i++) {
                    if (i % majorGridSpacing == 0) {
                        point.y = height * i;
                        t.transform(point, viewPoint);
                        g.drawLine((int) viewBounds.x, (int) viewPoint.y,
                                (int) (viewBounds.x + viewBounds.width), (int) viewPoint.y);
                    }
                }
            }
        }
    }

    public double constrainAngle(double angle) {
        // No step specified then no constraining
        if (theta == 0) {
            return angle;
        }

        double factor = Math.round(angle / theta);
        return theta * factor;
    }

    public double rotateAngle(double angle, RotationDirection dir) {
        // Check parameters
        if (dir == null) {
            throw new IllegalArgumentException("dir must not be null");
        }

        // Rotate into the specified direction by theta
        angle = constrainAngle(angle);
        switch (dir) {
            case CLOCKWISE :
                angle += theta;
                break;
            case COUNTER_CLOCKWISE :
            default: 
                angle -= theta;
                break;
        }
        return angle;
    }
}

