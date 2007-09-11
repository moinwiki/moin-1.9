/*
 * @(#)ConnectionFigure.java 5.1
 *
 */

package CH.ifa.draw.framework;

import java.awt.Point;
import java.io.Serializable;
import CH.ifa.draw.util.*;
import CH.ifa.draw.framework.*;

/**
 * Figures to connect Connectors provided by Figures.
 * A ConnectionFigure knows its start and end Connector.
 * It uses the Connectors to locate its connection points.<p>
 * A ConnectionFigure can have multiple segments. It provides
 * operations to split and join segments.
 *
 * <hr>
 * <b>Design Patterns</b><P>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld034.htm>Strategy</a></b><br>
 * Strategy is used encapsulate the algorithm to locate the connection point.
 * ConnectionFigure is the Strategy context and Connector is the Strategy.<br>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld026.htm>Observer</a></b><br>
 * Observer is used to track changes of the connected figures. A connection
 * figure registers itself as listeners or observers of the source and
 * target connector.
 * <hr>
 *
 * @see Connector
 */

public interface ConnectionFigure extends Figure, FigureChangeListener {

    /**
     * Sets the start Connector of the connection.
     * @param figure the start figure of the connection
     */
    public void connectStart(Connector start);

    /**
     * Sets the end Connector of the connection.
     * @param figure the end figure of the connection
     */
    public void connectEnd(Connector end);

    /**
     * Updates the connection
     */
    public void updateConnection();

    /**
     * Disconnects the start figure from the dependent figure
     */
    public void disconnectStart();

    /**
     * Disconnects the end figure from the dependent figure
     */
    public void disconnectEnd();

    /**
     * Gets the start Connector
     */
    public Connector start();

    /**
     * Gets the end Connector.
     */
    public Connector end();

    /**
     * Checks if two figures can be connected. Implement this method
     * to constrain the allowed connections between figures.
     */
    public boolean canConnect(Figure start, Figure end);

    /**
     * Checks if the ConnectionFigure connects the same figures.
     */
    public boolean connectsSame(ConnectionFigure other);

    /**
     * Sets the start point.
     */
    public void startPoint(int x, int y);

    /**
     * Sets the end point.
     */
    public void endPoint(int x, int y);

    /**
     * Gets the start point.
     */
    public Point startPoint();

    /**
     * Gets the end point.
     */
    public Point endPoint();

    /**
     * Sets the position of the point at the given position
     */
    public void setPointAt(Point p, int index);

    /**
     * Gets the Point at the given position
     */
    public Point pointAt(int index);

    /**
     * Gets the number of points or nodes of the connection
     */
    public int pointCount();

    /**
     * Splits the hit segment.
     * @param x, y the position where the figure should be split
     * @return the index of the splitting point
     */
    public int splitSegment(int x, int y);


    /**
     * Joins the hit segments.
     * @param x, y the position where the figure should be joined.
     * @return whether the segment was joined
     */
    public boolean joinSegments(int x, int y);
}
