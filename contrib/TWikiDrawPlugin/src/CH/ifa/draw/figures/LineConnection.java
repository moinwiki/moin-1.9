/*
 * @(#)LineConnection.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import java.util.*;
import java.io.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;
import CH.ifa.draw.util.*;

/**
 * A LineConnection is a standard implementation of the
 * ConnectionFigure interface. The interface is implemented with PolyLineFigure.
 * @see ConnectionFigure
 */
public  class LineConnection extends PolyLineFigure implements ConnectionFigure {

    protected Connector    fStart = null;
    protected Connector    fEnd = null;

    /*
     * Serialization support.
     */
    private static final long serialVersionUID = 6883731614578414801L;
    private int lineConnectionSerializedDataVersion = 1;

    /**
     * Constructs a LineConnection. A connection figure has
     * an arrow decoration at the start and end.
     */
    public LineConnection() {
        super(4);
        setStartDecoration(new ArrowTip());
        setEndDecoration(new ArrowTip());
    }

    /**
     * Tests whether a figure can be a connection target.
     * ConnectionFigures cannot be connected and return false.
     */
    public boolean canConnect() {
        return false;
    }

    /**
     * Ensures that a connection is updated if the connection
     * was moved.
     */
    protected void basicMoveBy(int dx, int dy) {
        // don't move the start and end point since they are connected
        for (int i = 1; i < fPoints.size()-1; i++)
            ((Point) fPoints.elementAt(i)).translate(dx, dy);

        updateConnection(); // make sure that we are still connected
    }

    /**
     * Sets the start figure of the connection.
     */
    public void connectStart(Connector start) {
        fStart = start;
        startFigure().addFigureChangeListener(this);
    }

    /**
     * Sets the end figure of the connection.
     */
    public void connectEnd(Connector end) {
        fEnd = end;
        endFigure().addFigureChangeListener(this);
        handleConnect(startFigure(), endFigure());
    }

    /**
     * Disconnects the start figure.
     */
    public void disconnectStart() {
        startFigure().removeFigureChangeListener(this);
        fStart = null;
    }

    /**
     * Disconnects the end figure.
     */
    public void disconnectEnd() {
        handleDisconnect(startFigure(), endFigure());
        endFigure().removeFigureChangeListener(this);
        fEnd = null;
    }

    /**
     * Tests whether a connection connects the same figures
     * as another ConnectionFigure.
     */
    public boolean connectsSame(ConnectionFigure other) {
        return other.start() == start() && other.end() == end();
    }

    /**
     * Handles the disconnection of a connection.
     * Override this method to handle this event.
     */
    protected void handleDisconnect(Figure start, Figure end) {}

    /**
     * Handles the connection of a connection.
     * Override this method to handle this event.
     */
    protected void handleConnect(Figure start, Figure end) {}

    /**
     * Gets the start figure of the connection.
     */
    public Figure startFigure() {
        if (start() != null)
            return start().owner();
        return null;
    }

    /**
     * Gets the end figure of the connection.
     */
    public Figure endFigure() {
        if (end() != null)
            return end().owner();
        return null;
    }

    /**
     * Gets the start figure of the connection.
     */
    public Connector start() {
        return fStart;
    }

    /**
     * Gets the end figure of the connection.
     */
    public Connector end() {
        return fEnd;
    }

    /**
     * Tests whether two figures can be connected.
     */
    public boolean canConnect(Figure start, Figure end) {
        return true;
    }

    /**
     * Sets the start point.
     */
    public void startPoint(int x, int y) {
        willChange();
        if (fPoints.size() == 0)
            fPoints.addElement(new Point(x, y));
        else
            fPoints.setElementAt(new Point(x, y), 0);
        changed();
    }

    /**
     * Sets the end point.
     */
    public void endPoint(int x, int y) {
        willChange();
        if (fPoints.size() < 2)
            fPoints.addElement(new Point(x, y));
        else
            fPoints.setElementAt(new Point(x, y), fPoints.size()-1);
        changed();
    }

    /**
     * Gets the start point.
     */
    public Point startPoint(){
        Point p = (Point)fPoints.firstElement();
        return new Point(p.x, p.y);
    }

    /**
     * Gets the end point.
     */
    public Point endPoint() {
        Point p = (Point)fPoints.lastElement();
        return new Point(p.x, p.y);
    }

    /**
     * Gets the handles of the figure. It returns the normal
     * PolyLineHandles but adds ChangeConnectionHandles at the
     * start and end.
     */
    public Vector handles() {
        Vector handles = new Vector(fPoints.size());
        handles.addElement(new ChangeConnectionStartHandle(this));
        for (int i = 1; i < fPoints.size()-1; i++)
            handles.addElement(new PolyLineHandle(this, locator(i), i));
        handles.addElement(new ChangeConnectionEndHandle(this));
        return handles;
    }

    /**
     * Sets the point and updates the connection.
     */
    public void setPointAt(Point p, int i) {
        super.setPointAt(p, i);
        layoutConnection();
    }

    /**
     * Inserts the point and updates the connection.
     */
    public void insertPointAt(Point p, int i) {
        super.insertPointAt(p, i);
        layoutConnection();
    }

    /**
     * Removes the point and updates the connection.
     */
    public void removePointAt(int i) {
        super.removePointAt(i);
        layoutConnection();
    }

    /**
     * Updates the connection.
     */
    public void updateConnection() {
        if (fStart != null) {
            Point start = fStart.findStart(this);
            startPoint(start.x, start.y);
        }
        if (fEnd != null) {
            Point end = fEnd.findEnd(this);
            endPoint(end.x, end.y);
        }
    }

    /**
     * Lays out the connection. This is called when the connection
     * itself changes. By default the connection is recalculated
     */
    public void layoutConnection() {
        updateConnection();
    }

    public void figureChanged(FigureChangeEvent e) {
        updateConnection();
    }

    public void figureRemoved(FigureChangeEvent e) {
        if (listener() != null)
            listener().figureRequestRemove(new FigureChangeEvent(this));
    }

    public void figureRequestRemove(FigureChangeEvent e) {}
    public void figureInvalidated(FigureChangeEvent e) {}
    public void figureRequestUpdate(FigureChangeEvent e) {}

    public void release() {
        super.release();
        handleDisconnect(startFigure(), endFigure());
        if (fStart != null) startFigure().removeFigureChangeListener(this);
        if (fEnd   != null) endFigure().removeFigureChangeListener(this);
    }

    public void write(StorableOutput dw) {
        super.write(dw);
        dw.writeStorable(fStart);
        dw.writeStorable(fEnd);
    }

    public void read(StorableInput dr) throws IOException {
        super.read(dr);
        Connector start = (Connector)dr.readStorable();
        if (start != null)
            connectStart(start);
        Connector end = (Connector)dr.readStorable();
        if (end != null)
            connectEnd(end);
        if (start != null && end != null)
            updateConnection();
    }

    private void readObject(ObjectInputStream s)
        throws ClassNotFoundException, IOException {

        s.defaultReadObject();

        if (fStart != null)
            connectStart(fStart);
        if (fEnd != null)
            connectEnd(fEnd);
    }
}
