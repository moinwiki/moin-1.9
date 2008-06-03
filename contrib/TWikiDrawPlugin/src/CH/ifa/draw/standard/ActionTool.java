/*
 * @(#)ActionTool.java 5.1
 *
 */

package CH.ifa.draw.standard;

import CH.ifa.draw.framework.*;

import java.awt.*;
import java.awt.event.MouseEvent;

/**
 * A tool that performs an action when it is active and
 * the mouse is clicked.
 */
public abstract class ActionTool extends AbstractTool {

    public ActionTool(DrawingView itsView) {
        super(itsView);
    }

    /**
     * Add the touched figure to the selection an invoke action
     * @see #action()
     */
    public void mouseDown(MouseEvent e, int x, int y) {
        Figure target = drawing().findFigure(x, y);
        if (target != null) {
            view().addToSelection(target);
            action(target);
        }
    }

    public void mouseUp(MouseEvent e, int x, int y) {
        editor().toolDone();
    }

    /**
     * Performs an action with the touched figure.
     */
    public abstract void action(Figure figure);
}
