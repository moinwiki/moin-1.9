/*
 * @(#)ScribbleTool.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import java.awt.event.MouseEvent;
import java.io.IOException;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.AbstractTool;

/**
 * Tool to scribble a PolyLineFigure
 * @see PolyLineFigure
 */
public class ScribbleTool extends AbstractTool {

    private PolyLineFigure  fScribble;
    private int             fLastX, fLastY;

    public ScribbleTool(DrawingView view) {
        super(view);
    }

    public void activate() {
        super.activate();
        fScribble = null;
    }

    public void deactivate() {
        super.deactivate();
        if (fScribble != null) {
            if (fScribble.size().width < 4 || fScribble.size().height < 4)
                drawing().remove(fScribble);
        }
    }

    private void point(int x, int y) {
        if (fScribble == null) {
            fScribble = new PolyLineFigure(x, y);
            view().add(fScribble);
        } else if (fLastX != x || fLastY != y)
            fScribble.addPoint(x, y);

        fLastX = x;
        fLastY = y;
    }

    public void mouseDown(MouseEvent e, int x, int y) {
        if (e.getClickCount() >= 2) {
            fScribble = null;
            editor().toolDone();
        }
        else {
            // use original event coordinates to avoid
            // supress that the scribble is constrained to
            // the grid
            point(e.getX(), e.getY());
        }
    }

    public void mouseDrag(MouseEvent e, int x, int y) {
        if (fScribble != null)
            point(e.getX(), e.getY());
    }
}
