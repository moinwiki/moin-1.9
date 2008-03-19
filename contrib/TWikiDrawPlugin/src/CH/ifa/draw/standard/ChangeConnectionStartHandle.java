/*
 * @(#)ChangeConnectionStartHandle.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.awt.Point;

import CH.ifa.draw.framework.*;

/**
 * Handle to reconnect the
 * start of a connection to another figure.
 */

public class ChangeConnectionStartHandle extends ChangeConnectionHandle {

    /**
     * Constructs the connection handle for the given start figure.
     */
    public ChangeConnectionStartHandle(Figure owner) {
        super(owner);
    }

    /**
     * Gets the start figure of a connection.
     */
    protected Connector target() {
        return fConnection.start();
    }

    /**
     * Disconnects the start figure.
     */
    protected void disconnect() {
        fConnection.disconnectStart();
    }

    /**
     * Sets the start of the connection.
     */
    protected void connect(Connector c) {
        fConnection.connectStart(c);
    }

    /**
     * Sets the start point of the connection.
     */
    protected void setPoint(int x, int y) {
        fConnection.startPoint(x, y);
    }

    /**
     * Returns the start point of the connection.
     */
    public Point locate() {
        return fConnection.startPoint();
    }
}
