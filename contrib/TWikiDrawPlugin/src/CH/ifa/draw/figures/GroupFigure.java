/*
 * @(#)GroupFigure.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
//import java.awt.geom.*;
import java.util.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;

/**
 * A Figure that groups a collection of figures.
 */
public  class GroupFigure extends CompositeFigure {

    /*
     * Serialization support.
     */
    private static final long serialVersionUID = 8311226373023297933L;
    private int groupFigureSerializedDataVersion = 1;

   /**
    * GroupFigures cannot be connected
    */
    public boolean canConnect() {
        return false;
    }

   /**
    * Gets the display box. The display box is defined as the union
    * of the contained figures.
    */
    public Rectangle displayBox() {
        FigureEnumeration k = figures();
        Rectangle r = k.nextFigure().displayBox();

        while (k.hasMoreElements())
            r.add(k.nextFigure().displayBox());
        return r;
    }

    /**
     * Transform all components proportionally.
     * Note that because components are position at integer
     * locations, we may get some odd-looking results!<p>
     * @author Crawford Currie, Motorola
     */
    public void basicDisplayBox(Point origin, Point corner) {
	Rectangle srcr = displayBox();
	Rectangle dstr = new Rectangle(
	    origin.x, origin.y,
	    corner.x - origin.x, corner.y - origin.y);

	if (srcr.equals(dstr) ||
	    corner.x <= origin.x || corner.y <= origin.y)
	    return;

	// Scaling transform
	double xtx = (double)(corner.x - origin.x) / srcr.width;
	double ytx = (double)(corner.y - origin.y) / srcr.height;

        FigureEnumeration k = figures();

        while (k.hasMoreElements()) {
	    Figure child = k.nextFigure();
	    Rectangle sr = child.displayBox();
	    Point childOrigin = new Point(
		(int)Math.round(dstr.x + (sr.x - srcr.x) * xtx),
		(int)Math.round(dstr.y + (sr.y - srcr.y) * ytx));
	    Point childCorner = new Point(
		(int)Math.round(childOrigin.x + sr.width * xtx),
		(int)Math.round(childOrigin.y + sr.height * ytx));
	    child.displayBox(childOrigin, childCorner);
	}
    }

    public FigureEnumeration decompose() {
        return new FigureEnumerator(fFigures);
    }

   /**
    * Gets the handles for the GroupFigure.
    */
    public Vector handles() {
        Vector handles = new Vector();
	// Handles changed to standard handles to support group scaling
	// Crawford Currie, Motorola
	BoxHandleKit.addCornerHandles(this, handles);
	/* Was:
	handles.addElement(new GroupHandle(this, RelativeLocator.northWest()));
        handles.addElement(new GroupHandle(this, RelativeLocator.northEast()));
        handles.addElement(new GroupHandle(this, RelativeLocator.southWest()));
        handles.addElement(new GroupHandle(this, RelativeLocator.southEast()));
	*/
        return handles;
    }

   /**
    * Sets the attribute of all the contained figures.
    */
    public void setAttribute(String name, Object value) {
        super.setAttribute(name, value);
        FigureEnumeration k = figures();
        while (k.hasMoreElements())
            k.nextFigure().setAttribute(name, value);
    }
}
