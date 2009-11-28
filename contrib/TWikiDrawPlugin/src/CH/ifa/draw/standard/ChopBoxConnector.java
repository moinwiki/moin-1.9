/*
 * @(#)ChopBoxConnector.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.awt.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.util.Geom;

/**
 * A ChopBoxConnector locates connection points by
 * choping the connection between the centers of the
 * two figures at the display box.
 * @see Connector
 */
public class ChopBoxConnector extends AbstractConnector {

    /*
     * Serialization support.
     */
    private static final long serialVersionUID = -1461450322712345462L;

    public ChopBoxConnector() { // only used for Storable implementation
    }

    public ChopBoxConnector(Figure owner) {
        super(owner);
    }

    public Point findStart(ConnectionFigure connection) {
        Figure startFigure = connection.start().owner();
        Rectangle r2 = connection.end().displayBox();
        Point r2c = null;

        if (connection.pointCount() == 2)
            r2c = new Point(r2.x + r2.width/2, r2.y + r2.height/2);
         else
            r2c = connection.pointAt(1);

        return chop(startFigure, r2c);
    }

    public Point findEnd(ConnectionFigure connection) {
        Figure endFigure = connection.end().owner();
        Rectangle r1 = connection.start().displayBox();
        Point r1c = null;

        if (connection.pointCount() == 2)
            r1c = new Point(r1.x + r1.width/2, r1.y + r1.height/2);
         else
            r1c = connection.pointAt(connection.pointCount()-2);

        return chop(endFigure, r1c);
    }

    protected Point chop(Figure target, Point from) {
        Rectangle r = target.displayBox();
        return Geom.angleToPoint(r, (Geom.pointToAngle(r, from)));
    }
}

