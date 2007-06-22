/*
 * @(#)ElbowTextLocator.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import java.util.*;
import java.io.IOException;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;
import CH.ifa.draw.util.*;

public class ElbowTextLocator extends AbstractLocator {
    public Point locate(Figure owner) {
        Point p = owner.center();
        Rectangle r = owner.displayBox();
        return new Point(p.x, p.y-10); // hack
    }
}
