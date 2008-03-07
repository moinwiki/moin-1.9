/*
 * @(#)Connector.java 5.1
 *
 */

package CH.ifa.draw.framework;

import java.awt.*;
import java.io.Serializable;

import CH.ifa.draw.util.*;

/**
 * Connectors know how to locate a connection point on a figure.
 * A Connector knows its owning figure and can determine either
 * the start or the endpoint of a given connection figure. A connector
 * has a display box that describes the area of a figure it is
 * responsible for. A connector can be visible but it doesn't have
 * to be.<br>
 * <hr>
 * <b>Design Patterns</b><P>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld004.htm>Strategy</a></b><br>
 * Connector implements the strategy to determine the connections points.<br>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld016.htm>Factory Method</a></b><br>
 * Connectors are created by the Figure's factory method connectorAt.
 * <hr>
 *
 * @see Figure#connectorAt
 * @see ConnectionFigure
 */
public interface Connector extends Serializable, Storable {

    /**
     * Finds the start point for the connection.
     */
    public abstract Point findStart(ConnectionFigure connection);

    /**
     * Finds the end point for the connection.
     */
    public abstract Point findEnd(ConnectionFigure connection);

    /**
     * Gets the connector's owner.
     */
    public abstract Figure owner();

    /**
     * Gets the display box of the connector.
     */
    public abstract Rectangle displayBox();

    /**
     * Tests if a point is contained in the connector.
     */
    public abstract boolean containsPoint(int x, int y);

    /**
     * Draws this connector. Connectors don't have to be visible
     * and it is OK leave this method empty.
     */
    public abstract void draw(Graphics g);

}

