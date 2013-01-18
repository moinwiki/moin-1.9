/*
 * @(#)ConnectionTool.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.awt.*;
import java.awt.event.MouseEvent;
import java.util.*;

import CH.ifa.draw.framework.*;
import CH.ifa.draw.util.Geom;

/**
 * A tool that can be used to connect figures, to split
 * connections, and to join two segments of a connection.
 * ConnectionTools turns the visibility of the Connectors
 * on when it enters a figure.
 * The connection object to be created is specified by a prototype.
 * <hr>
 * <b>Design Patterns</b><P>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld029.htm>Prototype</a></b><br>
 * ConnectionTools creates the connection by cloning a prototype.
 * <hr>
 *
 * @see ConnectionFigure
 * @see Object#clone
 */

public  class ConnectionTool extends AbstractTool {

    /**
     * the anchor point of the interaction
     */
    private Connector   fStartConnector;
    private Connector   fEndConnector;
    private Connector   fConnectorTarget = null;

    private Figure fTarget = null;

    /**
     * the currently created figure
     */
    private ConnectionFigure  fConnection;

    /**
     * the currently manipulated connection point
     */
    private int  fSplitPoint;

    /**
     * the currently edited connection
     */
    private ConnectionFigure  fEditedConnection = null;

    /**
     * the prototypical figure that is used to create new
     * connections.
     */
    private ConnectionFigure  fPrototype;


    public ConnectionTool(DrawingView view, ConnectionFigure prototype) {
        super(view);
        fPrototype = prototype;
    }

    /**
     * Handles mouse move events in the drawing view.
     */
    public void mouseMove(MouseEvent e, int x, int y) {
        trackConnectors(e, x, y);
    }

    /**
     * Manipulates connections in a context dependent way. If the
     * mouse down hits a figure start a new connection. If the mousedown
     * hits a connection split a segment or join two segments.
     */
    public void mouseDown(MouseEvent e, int x, int y)
    {
        int ex = e.getX();
        int ey = e.getY();
        fTarget = findConnectionStart(ex, ey, drawing());
        if (fTarget != null) {
            fStartConnector = findConnector(ex, ey, fTarget);
            if (fStartConnector != null) {
                Point p = new Point(ex, ey);
                fConnection = createConnection();
                fConnection.startPoint(p.x, p.y);
                fConnection.endPoint(p.x, p.y);
                view().add(fConnection);
            }
        }
        else {
            ConnectionFigure connection = findConnection(ex, ey, drawing());
            if (connection != null) {
                if (!connection.joinSegments(ex, ey)) {
                    fSplitPoint = connection.splitSegment(ex, ey);
                    fEditedConnection = connection;
                } else {
                    fEditedConnection = null;
                }
            }
        }
    }

    /**
     * Adjust the created connection or split segment.
     */
    public void mouseDrag(MouseEvent e, int x, int y) {
        Point p = new Point(e.getX(), e.getY());
        if (fConnection != null) {
            trackConnectors(e, x, y);
            if (fConnectorTarget != null)
                p = Geom.center(fConnectorTarget.displayBox());
            fConnection.endPoint(p.x, p.y);
        }
        else if (fEditedConnection != null) {
            Point pp = new Point(x, y);
            fEditedConnection.setPointAt(pp, fSplitPoint);
        }
    }

    /**
     * Connects the figures if the mouse is released over another
     * figure.
     */
    public void mouseUp(MouseEvent e, int x, int y) {
        Figure c = null;
        if (fStartConnector != null)
            c = findTarget(e.getX(), e.getY(), drawing());

        if (c != null) {
            fEndConnector = findConnector(e.getX(), e.getY(), c);
            if (fEndConnector != null) {
                fConnection.connectStart(fStartConnector);
                fConnection.connectEnd(fEndConnector);
                fConnection.updateConnection();
            }
        } else if (fConnection != null)
            view().remove(fConnection);

        fConnection = null;
        fStartConnector = fEndConnector = null;
        editor().toolDone();
    }

    public void deactivate() {
        super.deactivate();
        if (fTarget != null)
            fTarget.connectorVisibility(false);
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
     * Finds a connectable figure target.
     */
    protected Figure findSource(int x, int y, Drawing drawing) {
        return findConnectableFigure(x, y, drawing);
    }

    /**
     * Finds a connectable figure target.
     */
    protected Figure findTarget(int x, int y, Drawing drawing) {
        Figure target = findConnectableFigure(x, y, drawing);
        Figure start = fStartConnector.owner();

        if (target != null
             && fConnection != null
             && target.canConnect()
             && !target.includes(start)
             && fConnection.canConnect(start, target))
            return target;
        return null;
    }

    /**
     * Finds an existing connection figure.
     */
    protected ConnectionFigure findConnection(int x, int y, Drawing drawing) {
        Enumeration k = drawing.figuresReverse();
        while (k.hasMoreElements()) {
            Figure figure = (Figure) k.nextElement();
            figure = figure.findFigureInside(x, y);
            if (figure != null && (figure instanceof ConnectionFigure))
                return (ConnectionFigure)figure;
        }
        return null;
    }

    /**
     * Gets the currently created figure
     */
    protected ConnectionFigure createdFigure() {
        return fConnection;
    }

    protected void trackConnectors(MouseEvent e, int x, int y) {
        Figure c = null;

        if (fStartConnector == null)
            c = findSource(x, y, drawing());
        else
            c = findTarget(x, y, drawing());

        // track the figure containing the mouse
        if (c != fTarget) {
            if (fTarget != null)
                fTarget.connectorVisibility(false);
            fTarget = c;
            if (fTarget != null)
                fTarget.connectorVisibility(true);
        }

        Connector cc = null;
        if (c != null)
            cc = findConnector(e.getX(), e.getY(), c);
        if (cc != fConnectorTarget)
            fConnectorTarget = cc;

        view().checkDamage();
    }

    private Connector findConnector(int x, int y, Figure f) {
        return f.connectorAt(x, y);
    }

    /**
     * Finds a connection start figure.
     */
    protected Figure findConnectionStart(int x, int y, Drawing drawing) {
        Figure target = findConnectableFigure(x, y, drawing);
        if ((target != null) && target.canConnect())
            return target;
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

    protected Connector getStartConnector() {
        return fStartConnector;
    }

    protected Connector getEndConnector() {
        return fEndConnector;
    }

    protected Connector getTarget() {
        return fConnectorTarget;
    }

}
