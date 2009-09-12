/*
 * @(#)LocatorConnector.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.awt.*;
import java.io.IOException;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.util.*;

/**
 * A LocatorConnector locates connection points with
 * the help of a Locator. It supports the definition
 * of connection points to semantic locations.
 * @see Locator
 * @see Connector
 */
public class LocatorConnector extends AbstractConnector {

    /**
     * The standard size of the connector. The display box
     * is centered around the located point.
     */
    public static final int SIZE = 8;

    private Locator  fLocator;

    /*
     * Serialization support.
     */
    private static final long serialVersionUID = 5062833203337604181L;
    private int locatorConnectorSerializedDataVersion = 1;

    public LocatorConnector() { // only used for Storable
        fLocator = null;
    }

    public LocatorConnector(Figure owner, Locator l) {
        super(owner);
        fLocator = l;
    }

    protected Point locate(ConnectionFigure connection) {
        return fLocator.locate(owner());
    }

    /**
     * Tests if a point is contained in the connector.
     */
    public boolean containsPoint(int x, int y) {
        return displayBox().contains(x, y);
    }

    /**
     * Gets the display box of the connector.
     */
    public Rectangle displayBox() {
        Point p = fLocator.locate(owner());
        return new Rectangle(
                p.x - SIZE / 2,
                p.y - SIZE / 2,
                SIZE,
                SIZE);
    }

    /**
     * Draws this connector.
     */
    public void draw(Graphics g) {
        Rectangle r = displayBox();

        g.setColor(Color.blue);
        g.fillOval(r.x, r.y, r.width, r.height);
        g.setColor(Color.black);
        g.drawOval(r.x, r.y, r.width, r.height);
    }

    /**
     * Stores the arrow tip to a StorableOutput.
     */
    public void write(StorableOutput dw) {
        super.write(dw);
        dw.writeStorable(fLocator);
    }

    /**
     * Reads the arrow tip from a StorableInput.
     */
    public void read(StorableInput dr) throws IOException {
        super.read(dr);
        fLocator = (Locator)dr.readStorable();
    }

}

