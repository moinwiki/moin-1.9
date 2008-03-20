/*
 * @(#)DrawingChangeEvent.java 5.1
 *
 */

package CH.ifa.draw.framework;

import java.awt.Rectangle;
import java.util.EventObject;

/**
 * The event passed to DrawingChangeListeners.
 *
 */
public class DrawingChangeEvent extends EventObject {

    private Rectangle fRectangle;

    /**
     *  Constructs a drawing change event.
     */
    public DrawingChangeEvent(Drawing source, Rectangle r) {
        super(source);
        fRectangle = r;
    }

    /**
     *  Gets the changed drawing
     */
    public Drawing getDrawing() {
        return (Drawing)getSource();
    }

    /**
     *  Gets the changed rectangle
     */
    public Rectangle getInvalidatedRectangle() {
        return fRectangle;
    }
}
