/*
 * @(#)StandardDrawing.java 5.1
 *
 */

package CH.ifa.draw.standard;

import CH.ifa.draw.util.*;
import CH.ifa.draw.framework.*;
import java.awt.*;
import java.util.*;
import java.io.*;

/**
 * The standard implementation of the Drawing interface.
 *
 * @see Drawing
 */

public class StandardDrawing extends CompositeFigure implements Drawing {


    /**
     * the registered listeners
     */
    private transient Vector              fListeners;

    /**
     * boolean that serves as a condition variable
     * to lock the access to the drawing.
     * The lock is recursive and we keep track of the current
     * lock holder.
     */
    private transient Thread    fDrawingLockHolder = null;

    /*
     * Serialization support
     */
    private static final long serialVersionUID = -2602151437447962046L;
    private int drawingSerializedDataVersion = 1;

    /**
     * Constructs the Drawing.
     */
    public StandardDrawing() {
        super();
        fListeners = new Vector(2);
    }


    /**
     * Adds a listener for this drawing.
     */
    public void addDrawingChangeListener(DrawingChangeListener listener) {
        fListeners.addElement(listener);
    }

    /**
     * Removes a listener from this drawing.
     */
    public void removeDrawingChangeListener(DrawingChangeListener listener) {
        fListeners.removeElement(listener);
    }

    /**
     * Adds a listener for this drawing.
     */
    public Enumeration drawingChangeListeners() {
        return fListeners.elements();
    }

    /**
     * Removes the figure from the drawing and releases it.
     */

    public synchronized Figure remove(Figure figure) {
        // ensure that we remove the top level figure in a drawing
        if (figure.listener() != null) {
            figure.listener().figureRequestRemove(new FigureChangeEvent(figure, null));
            return figure;
        }
        return null;
    }


    /**
     * Handles a removeFromDrawing request that
     * is passed up the figure container hierarchy.
     * @see FigureChangeListener
     */
    public void figureRequestRemove(FigureChangeEvent e) {
        Figure figure = e.getFigure();
        if (fFigures.contains(figure)) {
            fFigures.removeElement(figure);
            figure.removeFromContainer(this);   // will invalidate figure
            figure.release();
        } else
            System.out.println("Attempt to remove non-existing figure");
    }

    /**
     * Invalidates a rectangle and merges it with the
     * existing damaged area.
     * @see FigureChangeListener
     */
    public void figureInvalidated(FigureChangeEvent e) {
        if (fListeners != null) {
            for (int i = 0; i < fListeners.size(); i++) {
                DrawingChangeListener l = (DrawingChangeListener)fListeners.elementAt(i);
                l.drawingInvalidated(new DrawingChangeEvent(this, e.getInvalidatedRectangle()));
            }
        }
    }

    /**
     * Forces an update
     */
    public void figureRequestUpdate(FigureChangeEvent e) {
        if (fListeners != null) {
            for (int i = 0; i < fListeners.size(); i++) {
                DrawingChangeListener l = (DrawingChangeListener)fListeners.elementAt(i);
                l.drawingRequestUpdate(new DrawingChangeEvent(this, null));
            }
        }
    }

    /**
     * Return's the figure's handles. This is only used when a drawing
     * is nested inside another drawing.
     */
    public Vector handles() {
        Vector handles = new Vector();
        handles.addElement(new NullHandle(this, RelativeLocator.northWest()));
        handles.addElement(new NullHandle(this, RelativeLocator.northEast()));
        handles.addElement(new NullHandle(this, RelativeLocator.southWest()));
        handles.addElement(new NullHandle(this, RelativeLocator.southEast()));
        return handles;
    }

    /**
     * Gets the display box. This is the union of all figures.
     */
    public Rectangle displayBox() {
        if (fFigures.size() > 0) {
            FigureEnumeration k = figures();

            Rectangle r = k.nextFigure().displayBox();

            while (k.hasMoreElements())
                r.add(k.nextFigure().displayBox());
            return r;
        }
        return new Rectangle(0, 0, 0, 0);
    }

    public void basicDisplayBox(Point p1, Point p2) {
    }

    /**
     * Acquires the drawing lock.
     */
    public synchronized void lock() {
        // recursive lock
        Thread current = Thread.currentThread();
        if (fDrawingLockHolder == current)
            return;
        while (fDrawingLockHolder != null) {
            try { wait(); } catch (InterruptedException ex) { }
        }
        fDrawingLockHolder = current;
    }

    /**
     * Releases the drawing lock.
     */
    public synchronized void unlock() {
        if (fDrawingLockHolder != null) {
            fDrawingLockHolder = null;
            notifyAll();
        }
    }

    private void readObject(ObjectInputStream s)
        throws ClassNotFoundException, IOException {

        s.defaultReadObject();

        fListeners = new Vector(2);
    }
}
