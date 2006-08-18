/*
 * @(#)HandleTracker.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.awt.*;
import java.awt.event.MouseEvent;
import CH.ifa.draw.framework.*;

/**
 * HandleTracker implements interactions with the handles
 * of a Figure.
 *
 * @see SelectionTool
 */
public class HandleTracker extends AbstractTool {

    private Handle  fAnchorHandle;

    public HandleTracker(DrawingView view, Handle anchorHandle) {
        super(view);
        fAnchorHandle = anchorHandle;
    }

    public void mouseDown(MouseEvent e, int x, int y) {
        super.mouseDown(e, x, y);
        fAnchorHandle.invokeStart(x, y, view());
    }

    public void mouseDrag(MouseEvent e, int x, int y) {
        super.mouseDrag(e, x, y);
        fAnchorHandle.invokeStep(x, y, fAnchorX, fAnchorY, view());
    }

    public void mouseUp(MouseEvent e, int x, int y) {
        super.mouseDrag(e, x, y);
        fAnchorHandle.invokeEnd(x, y, fAnchorX, fAnchorY, view());
    }
}
