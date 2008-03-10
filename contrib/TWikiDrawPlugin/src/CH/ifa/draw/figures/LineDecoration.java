/*
 * @(#)LineDecoration.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import java.io.Serializable;

import CH.ifa.draw.util.Storable;

/**
 * Decorate the start or end point of a line or poly line figure.
 * LineDecoration is the base class for the different line decorations.
 * @see PolyLineFigure
 */
public interface LineDecoration
                extends Storable, Cloneable, Serializable {

    /**
     * Draws the decoration in the direction specified by the two points.
     */
    public abstract void draw(Graphics g, int x1, int y1, int x2, int y2);
}
