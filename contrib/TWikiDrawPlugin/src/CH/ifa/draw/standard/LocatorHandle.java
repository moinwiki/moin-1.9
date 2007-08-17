/*
 * @(#)LocatorHandle.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.awt.Point;
import CH.ifa.draw.framework.*;

/**
 * A LocatorHandle implements a Handle by delegating the location requests to
 * a Locator object.
 *
 * @see Locator
 */

public class LocatorHandle extends AbstractHandle {

    private Locator       fLocator;

    /**
     * Initializes the LocatorHandle with the given Locator.
     */
    public LocatorHandle(Figure owner, Locator l) {
        super(owner);
        fLocator = l;
    }

    /**
     * Locates the handle on the figure by forwarding the request
     * to its figure.
     */
    public Point locate() {
        return fLocator.locate(owner());
    }
}
