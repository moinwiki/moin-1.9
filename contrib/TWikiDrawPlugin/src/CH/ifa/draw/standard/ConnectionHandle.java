/*
 * @(#)ConnectionHandle.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.awt.*;

import CH.ifa.draw.framework.*;
import CH.ifa.draw.util.Geom;

/**
 * A handle to connect figures.
 * The connection object to be created is specified by a prototype.
 * <hr>
 * <b>Design Patterns</b><P>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld029.htm>Prototype</a></b><br>
 * ConnectionHandle creates the connection by cloning a prototype.
 * <hr>
 *
 * @see ConnectionFigure
 * @see Object#clone
 */

public  class ConnectionHandle extends LocatorHandle {

    /**
     * the currently created connection
     */
    private ConnectionFigure fConnection;

    /**
     * the prototype of the connection to be created
     */
    private ConnectionFigure fPrototype;

    /**
     * the current target
     */
    private Figure fTarget = null;

    /**
     * Constructs a handle with the given owner, locator, and connection prototype
     */
    public ConnectionHandle(Figure owner, Locator l, ConnectionFigure prototype) {
        super(owner, l);
        fPrototype = prototype;
    }

    /**
     * Creates the connection
     */
    public void invokeStart(int  x, int  y, DrawingView view) {
        fConnection = createConnection();
        Point p = locate();
        fConnection.startPoint(p.x, p.y);
        fConnection.endPoint(p.x, p.y);
        view.drawing().add(fConnection);
    }

    /**
     * Tracks the connection.
     */
    public void invokeStep (int x, int y, int anchorX, int anchorY, DrawingView view) {
        Point p = new Point(x,y);
        Figure f = findConnectableFigure(x, y, view.drawing());
        // track the figure containing the mouse
        if (f != fTarget) {
            if (fTarget != null)
                fTarget.connectorVisibility(false);
            fTarget = f;
            if (fTarget != null)
                fTarget.connectorVisibility(true);
        }

        Connector target = findConnectionTarget(p.x, p.y, view.drawing());
        if (target != null)
            p = Geom.center(target.displayBox());
        fConnection.endPoint(p.x, p.y);
    }

    /**
     * Connects the figures if the mouse is released over another
     * figure.
     */
    public void invokeEnd(int x, int y, int anchorX, int anchorY, DrawingView view) {
        Connector target = findConnectionTarget(x, y, view.drawing());
        if (target != null) {
            fConnection.connectStart(startConnector());
            fConnection.connectEnd(target);
            fConnection.updateConnection();
        } else
            view.drawing().remove(fConnection);
        fConnection = null;
        if (fTarget != null) {
            fTarget.connectorVisibility(false);
            fTarget = null;
        }
    }

    private Connector startConnector() {
        Point p = locate();
        return owner().connectorAt(p.x, p.y);
    }

    /**
     * Creates the ConnectionFigure. By default the figure prototype is
     * cloned.
     */
    protected ConnectionFigure createConnection() {
		try {
			return (ConnectionFigure)fPrototype.clone();
		} catch (Exception e) {}
		return null;
    }

    /**
     * Finds a connection end figure.
     */
    protected Connector findConnectionTarget(int x, int y, Drawing drawing) {
        Figure target = findConnectableFigure(x, y, drawing);
        if ((target != null) && target.canConnect()
             && !target.includes(owner())
             && fConnection.canConnect(owner(), target)) {
                return findConnector(x, y, target);
        }
        return null;
    }

    private Figure findConnectableFigure(int x, int y, Drawing drawing) {
        FigureEnumeration k = drawing.figuresReverse();
        while (k.hasMoreElements()) {
            Figure figure = k.nextFigure();
            if (!figure.includes(fConnection) && figure.canConnect()) {
                if (figure.containsPoint(x, y))
                    return figure;
            }
        }
        return null;
    }

    protected Connector findConnector(int x, int y, Figure f) {
        return f.connectorAt(x, y);
    }


    /**
     * Draws the connection handle, by default the outline of a
     * blue circle.
     */
    public void draw(Graphics g) {
        Rectangle r = displayBox();
        g.setColor(Color.blue);
        g.drawOval(r.x, r.y, r.width, r.height);
    }

}
