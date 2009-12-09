/*
 * @(#)AbstractHandle.java 5.1
 *
 */

package CH.ifa.draw.standard;

import CH.ifa.draw.framework.*;
import java.awt.*;

/**
 * AbstractHandle provides defaulf implementation for the
 * Handle interface.
 *
 * @see Figure
 * @see Handle
 */
public abstract class AbstractHandle implements Handle {

    /**
     * The standard size of a handle.
     */
    public static final int HANDLESIZE = 8;
    private Figure fOwner;

    /**
     * Initializes the owner of the figure.
     */
    public AbstractHandle(Figure owner) {
        fOwner = owner;
    }

    /**
     * Locates the handle on the figure. The handle is drawn
     * centered around the returned point.
     */
    public abstract Point locate();

    /**
     * @ deprecated As of version 4.1,
     * use invokeStart(x, y, drawingView)
     * Tracks the start of the interaction. The default implementation
     * does nothing.
     * @param x the x position where the interaction started
     * @param y the y position where the interaction started
     */
    public void invokeStart(int  x, int  y, Drawing drawing) { }

    /**
     * @ deprecated As of version 4.1,
     * use invokeStart(x, y, drawingView)
     * Tracks the start of the interaction. The default implementation
     * does nothing.
     * @param x the x position where the interaction started
     * @param y the y position where the interaction started
     * @param view the handles container
     */
    public void invokeStart(int  x, int  y, DrawingView view) {
        invokeStart(x, y, view.drawing());
    }

    /**
     * @ deprecated As of version 4.1,
     * use invokeStep(x, y, anchorX, anchorY, drawingView)
     *
     * Tracks a step of the interaction.
     * @param dx x delta of this step
     * @param dy y delta of this step
     */
    public void invokeStep (int dx, int dy, Drawing drawing) { }

    /**
     * Tracks a step of the interaction.
     * @param x the current x position
     * @param y the current y position
     * @param anchorX the x position where the interaction started
     * @param anchorY the y position where the interaction started
     */
    public void invokeStep (int x, int y, int anchorX, int anchorY, DrawingView view) {
        invokeStep(x-anchorX, y-anchorY, view.drawing());
    }

    /**
     * Tracks the end of the interaction.
     * @param x the current x position
     * @param y the current y position
     * @param anchorX the x position where the interaction started
     * @param anchorY the y position where the interaction started
     */
    public void invokeEnd(int x, int y, int anchorX, int anchorY, DrawingView view) {
        invokeEnd(x-anchorX, y-anchorY, view.drawing());
    }

    /**
     * @deprecated As of version 4.1,
     * use invokeEnd(x, y, anchorX, anchorY, drawingView).
     *
     * Tracks the end of the interaction.
     */
    public void invokeEnd  (int dx, int dy, Drawing drawing) { }

    /**
     * Gets the handle's owner.
     */
    public Figure owner() {
        return fOwner;
    }

    /**
     * Gets the display box of the handle.
     */
    public Rectangle displayBox() {
        Point p = locate();
        return new Rectangle(
                p.x - HANDLESIZE / 2,
                p.y - HANDLESIZE / 2,
                HANDLESIZE,
                HANDLESIZE);
    }

    /**
     * Tests if a point is contained in the handle.
     */
    public boolean containsPoint(int x, int y) {
        return displayBox().contains(x, y);
    }

    /**
     * Draws this handle.
     */
    public void draw(Graphics g) {
        Rectangle r = displayBox();

        g.setColor(Color.white);
        g.fillRect(r.x, r.y, r.width, r.height);

        g.setColor(Color.black);
        g.drawRect(r.x, r.y, r.width, r.height);
    }
}


