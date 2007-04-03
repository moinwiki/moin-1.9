/*
 * @(#)PolyLineHandle.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.LocatorHandle;

/**
 * A handle for a node on the polyline.
 */
public class PolyLineHandle extends LocatorHandle {

    private int fIndex;
    private Point fAnchor;

   /**
    * Constructs a poly line handle.
    * @param owner the owning polyline figure.
    * @l the locator
    * @index the index of the node associated with this handle.
    */
    public PolyLineHandle(PolyLineFigure owner, Locator l, int index) {
        super(owner, l);
        fIndex = index;
    }

    public void invokeStart(int  x, int  y, DrawingView view) {
        fAnchor = new Point(x, y);
    }

    public void invokeStep (int x, int y, int anchorX, int anchorY, DrawingView view) {
        myOwner().setPointAt(new Point(x, y), fIndex);
    }

    private PolyLineFigure myOwner() {
        return (PolyLineFigure)owner();
    }
}


