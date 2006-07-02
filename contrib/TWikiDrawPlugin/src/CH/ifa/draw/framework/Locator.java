/*
 * @(#)Locator.java 5.1
 *
 */

package CH.ifa.draw.framework;

import CH.ifa.draw.util.Storable;
import java.awt.*;
import java.io.Serializable;

/**
 * Locators can be used to locate a position on a figure.<p>
 *
 * <hr>
 * <b>Design Patterns</b><P>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld034.htm>Strategy</a></b><br>
 * Locator encapsulates the strategy to locate a handle on a figure.
 */

public interface Locator extends Storable, Serializable, Cloneable {

    /**
     * Locates a position on the passed figure.
     * @return a point on the figure.
     */
    public Point locate(Figure owner);
}

