/*
 * @(#)GroupHandle.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.NullHandle;

/**
 * A Handle for a GroupFigure.
 */
final class GroupHandle extends NullHandle {

    public GroupHandle(Figure owner, Locator locator) {
        super(owner, locator);
    }

    /**
     * Draws the Group handle.
     */
    public void draw(Graphics g) {
        Rectangle r = displayBox();

        g.setColor(Color.black);
        g.drawRect(r.x, r.y, r.width, r.height);
        r.grow(-1,-1);
        g.setColor(Color.white);
        g.drawRect(r.x, r.y, r.width, r.height);
    }
}
