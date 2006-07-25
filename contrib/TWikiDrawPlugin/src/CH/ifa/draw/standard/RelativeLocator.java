/*
 * @(#)RelativeLocator.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.awt.*;
import java.io.IOException;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.util.*;

/**
 * A locator that specfies a point that is relative to the bounds
 * of a figure.
 * @see Locator
 */
public class RelativeLocator extends AbstractLocator {
    /*
     * Serialization support.
     */
    private static final long serialVersionUID = 2619148876087898602L;
    private int relativeLocatorSerializedDataVersion = 1;

    double  fRelativeX;
    double  fRelativeY;

    public RelativeLocator() {
        fRelativeX = 0.0;
        fRelativeY = 0.0;
    }

    public RelativeLocator(double relativeX, double relativeY) {
        fRelativeX = relativeX;
        fRelativeY = relativeY;
    }

    public Point locate(Figure owner) {
        Rectangle r = owner.displayBox();
        return new Point(
            r.x + (int)(r.width*fRelativeX),
            r.y + (int)(r.height*fRelativeY)
        );
    }

    public void write(StorableOutput dw) {
        super.write(dw);
        dw.writeDouble(fRelativeX);
        dw.writeDouble(fRelativeY);
    }

    public void read(StorableInput dr) throws IOException {
        super.read(dr);
        fRelativeX = dr.readDouble();
        fRelativeY = dr.readDouble();
    }

    static public Locator east() {
        return new RelativeLocator(1.0, 0.5);
    }

    /**
     * North.
     */
    static public Locator north() {
        return new RelativeLocator(0.5, 0.0);
    }

    /**
     * West.
     */
    static public Locator west() {
        return new RelativeLocator(0.0, 0.5);
    }

    /**
     * North east.
     */
    static public Locator northEast() {
        return new RelativeLocator(1.0, 0.0);
    }

    /**
     * North west.
     */
    static public Locator northWest() {
        return new RelativeLocator(0.0, 0.0);
    }

    /**
     * South.
     */
    static public Locator south() {
        return new RelativeLocator(0.5, 1.0);
    }

    /**
     * South east.
     */
    static public Locator southEast() {
        return new RelativeLocator(1.0, 1.0);
    }

    /**
     * South west.
     */
    static public Locator southWest() {
        return new RelativeLocator(0.0, 1.0);
    }

    /**
     * Center.
     */
    static public Locator center() {
        return new RelativeLocator(0.5, 0.5);
    }

}
