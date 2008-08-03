/*
 * @(#)ChangeConnectionEndHandle.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.awt.Point;

import CH.ifa.draw.framework.*;

/**
 * A handle to reconnect the end point of
 * a connection to another figure.
 */

public class ChangeConnectionEndHandle extends ChangeConnectionHandle {

    /**
     * Constructs the connection handle.
     */
    public ChangeConnectionEndHandle(Figure owner) {
        super(owner);
    }

    /**
     * Gets the end figure of a connection.
     */
    protected Connector target() {
        return fConnection.end();
    }

    /**
     * Disconnects the end figure.
     */
    protected void disconnect() {
        fConnection.disconnectEnd();
    }

    /**
     * Sets the end of the connection.
     */
    protected void connect(Connector c) {
        fConnection.connectEnd(c);
    }

    /**
     * Sets the end point of the connection.
     */
    protected void setPoint(int x, int y) {
        fConnection.endPoint(x, y);
    }

    /**
     * Returns the end point of the connection.
     */
    public Point locate() {
        return fConnection.endPoint();
    }
}

