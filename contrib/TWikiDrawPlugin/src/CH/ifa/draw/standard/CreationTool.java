/*
 * @(#)CreationTool.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.awt.*;
import java.awt.event.MouseEvent;

import CH.ifa.draw.framework.*;

/**
 * A tool to create new figures. The figure to be
 * created is specified by a prototype.
 *
 * <hr>
 * <b>Design Patterns</b><P>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld029.htm>Prototype</a></b><br>
 * CreationTool creates new figures by cloning a prototype.
 * <hr>
 * @see Figure
 * @see Object#clone
 */


public class CreationTool extends AbstractTool {

    /**
     * the anchor point of the interaction
     */
    private Point   fAnchorPoint;

    /**
     * the currently created figure
     */
    private Figure  fCreatedFigure;

    /**
     * the prototypical figure that is used to create new figures.
     */
    private Figure  fPrototype;


    /**
     * Initializes a CreationTool with the given prototype.
     */
    public CreationTool(DrawingView view, Figure prototype) {
        super(view);
        fPrototype = prototype;
    }

    /**
     * Constructs a CreationTool without a prototype.
     * This is for subclassers overriding createFigure.
     */
    protected CreationTool(DrawingView view) {
        super(view);
        fPrototype = null;
    }

    /**
     * Sets the cross hair cursor.
     */
    public void activate() {
        view().setCursor(Cursor.getPredefinedCursor(Cursor.CROSSHAIR_CURSOR));
    }

    /**
     * Creates a new figure by cloning the prototype.
     */
    public void mouseDown(MouseEvent e, int x, int y) {
        fAnchorPoint = new Point(x,y);
        fCreatedFigure = createFigure();
        fCreatedFigure.displayBox(fAnchorPoint, fAnchorPoint);
        view().add(fCreatedFigure);
    }

    /**
     * Creates a new figure by cloning the prototype.
     */
    protected Figure createFigure() {
        if (fPrototype == null)
		    throw new HJDError("No protoype defined");
        return (Figure) fPrototype.clone();
    }

    /**
     * Adjusts the extent of the created figure
     */
    public void mouseDrag(MouseEvent e, int x, int y) {
        fCreatedFigure.displayBox(fAnchorPoint, new Point(x,y));
    }

    /**
     * Checks if the created figure is empty. If it is, the figure
     * is removed from the drawing.
     * @see Figure#isEmpty
     */
    public void mouseUp(MouseEvent e, int x, int y) {
        if (fCreatedFigure.isEmpty())
            drawing().remove(fCreatedFigure);
        fCreatedFigure = null;
        editor().toolDone();
    }

    /**
     * Gets the currently created figure
     */
    protected Figure createdFigure() {
        return fCreatedFigure;
    }
}
