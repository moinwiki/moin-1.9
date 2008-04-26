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

    boolean     fConnected = false;

    public ConnectedTextTool(DrawingView view, Figure prototype) {
        super(view, prototype);
    }

    /**
     * If the pressed figure is a TextHolder it can be edited otherwise
     * a new text figure is created.
     */
    public void mouseDown(MouseEvent e, int x, int y) {
        super.mouseDown(e, x, y);

	    Figure pressedFigure =  drawing().findFigureInside(x, y);

	    TextHolder textHolder = (TextHolder)createdFigure();
        if (!fConnected && pressedFigure != null &&
                     textHolder != null && pressedFigure != textHolder) {
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

