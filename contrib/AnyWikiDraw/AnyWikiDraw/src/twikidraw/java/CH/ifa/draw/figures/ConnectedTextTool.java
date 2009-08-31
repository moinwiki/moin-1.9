/*
 * @(#)ConnectedTextTool.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import java.awt.event.MouseEvent;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;

/**
 * Tool to create new or edit existing text figures.
 * A new text figure is connected with the clicked figure.
 *
 * @see TextHolder
 */
public  class ConnectedTextTool extends TextTool {

    private boolean     fConnected = false;

    public ConnectedTextTool(DrawingView view, Figure prototype) {
        super(view, prototype);
    }

    /**
     * If the pressed figure is a TextHolder it can be edited otherwise
     * a new text figure is created.
     */
    public void mouseDown(MouseEvent e, int x, int y) {
        super.mouseDown(e, x, y);

	    Figure pressedFigure = drawing().findFigureInside(x, y);

	    TextHolder textHolder = (TextHolder)createdFigure();
        if (!fConnected &&
            pressedFigure != null &&
            textHolder != null &&
            pressedFigure != textHolder &&
            // As near as I can figure it, if you use the default
            // JHotDraw code below then there is a case where you
            // can end up here with a TextHolder you are just starting
            // to edit as the pressedFigure, and still set as the
            // createdFigure (because the mouseUp gets missed, I guess?)
            // Anyway, the upshot is that the text you just created
            // gets detached from the object you created it on and
            // attached to the figure you just started editing instead.
            // The following two lines are a hack to avoid this, but they
            // seem to work. CC 8/3/05
            !((pressedFigure instanceof TextHolder) &&
              ((TextHolder) pressedFigure).acceptsTyping())) {
            textHolder.connect(pressedFigure);
            fConnected = true;
        }
    }

    /**
     * If the pressed figure is a TextHolder it can be edited otherwise
     * a new text figure is created.
     */
    public void activate() {
        fConnected = false;
    }
}

