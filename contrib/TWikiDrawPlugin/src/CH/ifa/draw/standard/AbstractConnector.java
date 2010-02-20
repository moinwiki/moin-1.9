/*
 * @(#)AbstractConnector.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.awt.*;
import java.io.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.util.*;

/**
 * AbstractConnector provides default implementation for
 * the Connector interface.
 * @see Connector
 */
public abstract class AbstractConnector implements Connector {
    /**
     * the owner of the connector
     */
    private Figure      fOwner;

    /*
     * Serialization support.
     */
    private static final long serialVersionUID = -5170007865562687545L;
    private int abstractConnectorSerializedDataVersion = 1;

    /**
     * Constructs a connector that has no owner. It is only
     * used internally to resurrect a connectors from a
     * StorableOutput. It should never be called directly.
     */
    public AbstractConnector() {
        fOwner = null;
    }

    /**
     * Constructs a connector with the given owner figure.
     */
    public AbstractConnector(Figure owner) {
        fOwner = owner;
    }

    /**
     * Gets the connector's owner.
     */
    public Figure owner() {
        return fOwner;
    }

    public Point findStart(ConnectionFigure connection) {
        return findPoint(connection);
    }

    public Point findEnd(ConnectionFigure connection) {
        return findPoint(connection);
    }

    /**
     * Gets the connection point. Override when the connector
     * does not need to distinguish between the start and end
     * point of a connection.
     */
    protected Point findPoint(ConnectionFigure connection) {
        return Geom.center(displayBox());
    }

    /**
     * Gets the display box of the connector.
     */
    public Rectangle displayBox() {
        return owner().displayBox();
    }

    /**
     * Tests if a point is contained in the connector.
     */
    public boolean containsPoint(int x, int y) {
        return owner().containsPoint(x, y);
    }

    /**
     * Draws this connector. By default connectors are invisible.
     */
    public void draw(Graphics g) {
        // invisible by default
    }

    /**
     * Stores the connector and its owner to a StorableOutput.
     */
    public void write(StorableOutput dw) {
        dw.writeStorable(fOwner);
    }

    public String getMap() {
	return "";
    }

    /**
     * Reads the connector and its owner from a StorableInput.
     */
    public void read(StorableInput dr) throws IOException {
        fOwner = (Figure)dr.readStorable();
    }

}

