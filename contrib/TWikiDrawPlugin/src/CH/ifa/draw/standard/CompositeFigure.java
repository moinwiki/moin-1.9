/*
 * @(#)CompositeFigure.java 5.1
 *
 */

package CH.ifa.draw.standard;

import CH.ifa.draw.util.*;
import CH.ifa.draw.framework.*;
import java.awt.*;
import java.util.*;
import java.io.*;

/**
 * A Figure that is composed of several figures. A CompositeFigure
 * doesn't define any layout behavior. It is up to subclassers to
 * arrange the contained figures.
 * <hr>
 * <b>Design Patterns</b><P>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld012.htm>Composite</a></b><br>
 * CompositeFigure enables to treat a composition of figures like
 * a single figure.<br>
 * @see Figure
 */

public abstract class CompositeFigure
                extends AbstractFigure
                implements FigureChangeListener {

    /**
     * The figures that this figure is composed of
     * @see #add
     * @see #remove
     */
    protected Vector fFigures;

    /*
     * Serialization support.
     */
    private static final long serialVersionUID = 7408153435700021866L;
    private int compositeFigureSerializedDataVersion = 1;

    protected CompositeFigure() {
        fFigures = new Vector();
    }

    /**
     * Adds a figure to the list of figures. Initializes the
     * the figure's container.
     */
    public Figure add(Figure figure) {
        if (!fFigures.contains(figure)) {
            fFigures.addElement(figure);
            figure.addToContainer(this);
        }
        return figure;
    }

    /**
     * Adds a vector of figures.
     * @see #add
     */
    public void addAll(Vector newFigures) {
        Enumeration k = newFigures.elements();
        while (k.hasMoreElements())
            add((Figure) k.nextElement());
    }

    /**
     * Removes a figure from the composite.
     * @see #removeAll
     */
    public Figure remove(Figure figure) {
        if (fFigures.contains(figure)) {
            figure.removeFromContainer(this);
            fFigures.removeElement(figure);
        }
        return figure;
    }

    /**
     * Removes a vector of figures.
     * @see #remove
     */
    public void removeAll(Vector figures) {
        Enumeration k = figures.elements();
        while (k.hasMoreElements())
            remove((Figure) k.nextElement());
    }

    /**
     * Removes all children.
     * @see #remove
     */
    public void removeAll() {
        FigureEnumeration k = figures();
        while (k.hasMoreElements()) {
            Figure figure = k.nextFigure();
            figure.removeFromContainer(this);
        }
        fFigures.removeAllElements();
    }

    /**
     * Removes a figure from the figure list, but
     * doesn't release it. Use this method to temporarily
     * manipulate a figure outside of the drawing.
     */
    public synchronized Figure orphan(Figure figure) {
        fFigures.removeElement(figure);
        return figure;
    }

    /**
     * Removes a vector of figures from the figure's list
     * without releasing the figures.
     * @see orphan
     */
    public void orphanAll(Vector newFigures) {
        Enumeration k = newFigures.elements();
        while (k.hasMoreElements())
            orphan((Figure) k.nextElement());
    }

    /**
     * Replaces a figure in the drawing without
     * removing it from the drawing.
     */
    public synchronized void replace(Figure figure, Figure replacement) {
        int index = fFigures.indexOf(figure);
        if (index != -1) {
            replacement.addToContainer(this);   // will invalidate figure
            figure.changed();
            fFigures.setElementAt(replacement, index);
        }
    }

    /**
     * Sends a figure to the back of the drawing.
     */
    public synchronized void sendToBack(Figure figure) {
        if (fFigures.contains(figure)) {
            fFigures.removeElement(figure);
            fFigures.insertElementAt(figure,0);
            figure.changed();
        }
    }

    /**
     * Brings a figure to the front.
     */
    public synchronized void bringToFront(Figure figure) {
        if (fFigures.contains(figure)) {
            fFigures.removeElement(figure);
            fFigures.addElement(figure);
            figure.changed();
        }
    }

    /**
     * Draws all the contained figures
     * @see Figure#draw
     */
    public void draw(Graphics g, boolean showGuides) {
        FigureEnumeration k = figures();
        while (k.hasMoreElements())
            k.nextFigure().draw(g, showGuides);
    }

    /**
     * Gets a figure at the given index.
     */
    public Figure figureAt(int i) {
        return (Figure)fFigures.elementAt(i);
    }

    /**
     * Returns an Enumeration for accessing the contained figures.
     * The figures are returned in the drawing order.
     */
    public final FigureEnumeration figures() {
        return new FigureEnumerator(fFigures);
    }

    /**
     * Gets number of child figures.
     */
    public int figureCount() {
        return fFigures.size();
    }

    /**
     * Returns an Enumeration for accessing the contained figures
     * in the reverse drawing order.
     */
    public final FigureEnumeration figuresReverse() {
        return new ReverseFigureEnumerator(fFigures);
    }

    /**
     * Finds a top level Figure. Use this call for hit detection that
     * should not descend into the figure's children.
     */
    public Figure findFigure(int x, int y) {
        FigureEnumeration k = figuresReverse();
        while (k.hasMoreElements()) {
            Figure figure = k.nextFigure();
            if (figure.containsPoint(x, y))
                return figure;
        }
        return null;
    }

    /**
     * Finds a top level Figure that intersects the given rectangle.
     */
    public Figure findFigure(Rectangle r) {
        FigureEnumeration k = figuresReverse();
        while (k.hasMoreElements()) {
            Figure figure = k.nextFigure();
            Rectangle fr = figure.displayBox();
            if (r.intersects(fr))
                return figure;
        }
        return null;
    }

    /**
     * Finds a top level Figure, but supresses the passed
     * in figure. Use this method to ignore a figure
     * that is temporarily inserted into the drawing.
     * @param x the x coordinate
     * @param y the y coordinate
     * @param without the figure to be ignored during
     * the find.
     */
    public Figure findFigureWithout(int x, int y, Figure without) {
        if (without == null)
            return findFigure(x, y);
        FigureEnumeration k = figuresReverse();
        while (k.hasMoreElements()) {
            Figure figure = k.nextFigure();
            if (figure.containsPoint(x, y) && !figure.includes(without))
                return figure;
        }
        return null;
    }

    /**
     * Finds a top level Figure that intersects the given rectangle.
     * It supresses the passed
     * in figure. Use this method to ignore a figure
     * that is temporarily inserted into the drawing.
     */
    public Figure findFigure(Rectangle r, Figure without) {
        if (without == null)
            return findFigure(r);
        FigureEnumeration k = figuresReverse();
        while (k.hasMoreElements()) {
            Figure figure = k.nextFigure();
            Rectangle fr = figure.displayBox();
            if (r.intersects(fr) && !figure.includes(without))
                return figure;
        }
        return null;
    }

    /**
     * Finds a figure but descends into a figure's
     * children. Use this method to implement <i>click-through</i>
     * hit detection, that is, you want to detect the inner most
     * figure containing the given point.
     */
    public Figure findFigureInside(int x, int y) {
        FigureEnumeration k = figuresReverse();
        while (k.hasMoreElements()) {
            Figure figure = k.nextFigure().findFigureInside(x, y);
            if (figure != null)
                return figure;
        }
        return null;
    }

    /**
     * Finds a figure but descends into a figure's
     * children. It supresses the passed
     * in figure. Use this method to ignore a figure
     * that is temporarily inserted into the drawing.
     */
    public Figure findFigureInsideWithout(int x, int y, Figure without) {
        FigureEnumeration k = figuresReverse();
        while (k.hasMoreElements()) {
            Figure figure = k.nextFigure();
            if (figure != without) {
                Figure found = figure.findFigureInside(x, y);
                if (found != null)
                    return found;
            }
        }
        return null;
    }

    /**
     * Checks if the composite figure has the argument as one of
     * its children.
     */
    public boolean includes(Figure figure) {
        if (super.includes(figure))
            return true;

        FigureEnumeration k = figures();
        while (k.hasMoreElements()) {
            Figure f = k.nextFigure();
            if (f.includes(figure))
                return true;
        }
        return false;
    }

    /**
     * Moves all the given figures by x and y. Doesn't announce
     * any changes. Subclassers override
     * basicMoveBy. Clients usually call moveBy.
     * @see moveBy
     */
    protected void basicMoveBy(int x, int y) {
        FigureEnumeration k = figures();
        while (k.hasMoreElements()) {
            Figure fig = k.nextFigure();
            Figure obsrvd = (Figure) fig.getAttribute("observed.figure");
            if (obsrvd == null || !includes(obsrvd)) {
                fig.moveBy(x, y);
            }
        }
    }

    /**
     * Releases the figure and all its children.
     */
    public void release() {
        super.release();
        FigureEnumeration k = figures();
        while (k.hasMoreElements()) {
            Figure figure = k.nextFigure();
            figure.release();
        }
    }

    /**
     * Propagates the figureInvalidated event to my listener.
     * @see FigureChangeListener
     */
    public void figureInvalidated(FigureChangeEvent e) {
        if (listener() != null)
            listener().figureInvalidated(e);
    }

    /**
     * Propagates the removeFromDrawing request up to the container.
     * @see FigureChangeListener
     */
    public void figureRequestRemove(FigureChangeEvent e) {
        if (listener() != null)
            listener().figureRequestRemove(new FigureChangeEvent(this));
    }

    /**
     * Propagates the requestUpdate request up to the container.
     * @see FigureChangeListener
     */
    public void figureRequestUpdate(FigureChangeEvent e) {
        if (listener() != null)
            listener().figureRequestUpdate(e);
    }

    public void figureChanged(FigureChangeEvent e) {
    }

    public void figureRemoved(FigureChangeEvent e) {
    }

    /**
     * Writes the contained figures to the StorableOutput.
     */
    public void write(StorableOutput dw) {
        super.write(dw);
        dw.writeInt(fFigures.size());
        Enumeration k = fFigures.elements();
        while (k.hasMoreElements())
            dw.writeStorable((Storable) k.nextElement());
    }

    public String getMap() {
	String areas = "";
        Enumeration k = fFigures.elements();
        while (k.hasMoreElements())
            areas = ((Storable) k.nextElement()).getMap() + areas;
	return areas;
    }

    /**
     * Reads the contained figures from StorableInput.
     */
    public void read(StorableInput dr) throws IOException {
        super.read(dr);
        int size = dr.readInt();
        fFigures = new Vector(size);
        for (int i=0; i<size; i++)
            add((Figure)dr.readStorable());
    }

    private void readObject(ObjectInputStream s)
        throws ClassNotFoundException, IOException {

        s.defaultReadObject();

        FigureEnumeration k = figures();
        while (k.hasMoreElements()) {
            Figure figure = k.nextFigure();
            figure.addToContainer(this);
        }
    }
}
