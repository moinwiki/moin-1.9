/*
 * @(#)FigureChangeEvent.java 5.1
 *
 */

package CH.ifa.draw.framework;

import java.awt.Rectangle;
import java.util.EventObject;

/**
 * FigureChange event passed to FigureChangeListeners.
 *
 */
public class FigureChangeEvent extends EventObject {

    private Rectangle fRectangle;
    private static final Rectangle  fgEmptyRectangle = new Rectangle(0, 0, 0, 0);

   /**
    * Constructs an event for the given source Figure. The rectangle is the
    * area to be invalvidated.
    */
    public FigureChangeEvent(Figure source, Rectangle r) {
        super(source);
        fRectangle = r;
    }

    public FigureChangeEvent(Figure source) {
        super(source);
        fRectangle = fgEmptyRectangle;
    }

    /**
     *  Gets the changed figure
     */
    public Figure getFigure() {
        return (Figure)getSource();
    }

    /**
     *  Gets the changed rectangle
     */
    public Rectangle getInvalidatedRectangle() {
        return fRectangle;
    }
}
