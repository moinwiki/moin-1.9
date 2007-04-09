/*
 * @(#)DrawingChangeListener.java 5.1
 *
 */

package CH.ifa.draw.framework;

import java.awt.Rectangle;
import java.util.EventListener;

/**
 * Listener interested in Drawing changes.
 */
public interface DrawingChangeListener extends EventListener {

    /**
     *  Sent when an area is invalid
     */
    public void drawingInvalidated(DrawingChangeEvent e);

    /**
     *  Sent when the drawing wants to be refreshed
     */
    public void drawingRequestUpdate(DrawingChangeEvent e);
}
