/*
 * Sat Mar  1 09:06:09 1997  Doug Lea  (dl at gee)
 * Based on RadiusHandle
 */

package CH.ifa.draw.contrib;

import java.awt.*;
import java.util.*;
import java.io.IOException;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.util.*;
import CH.ifa.draw.standard.*;


/**
 * A Handle to scale and rotate a PolygonFigure
 */
class PolygonScaleHandle extends AbstractHandle {

  private Point fOrigin = null;
  private Point fCurrent = null;
  private Polygon fOrigPoly = null;

  public PolygonScaleHandle(PolygonFigure owner) {
    super(owner);
 }

  public void invokeStart(int  x, int  y, Drawing drawing) {
    fOrigPoly = ((PolygonFigure)(owner())).getPolygon();
    fOrigin = getOrigin();
    fCurrent = new Point(fOrigin.x, fOrigin.y);
  }

  public void invokeStep (int dx, int dy, Drawing drawing) {
    fCurrent = new Point(fOrigin.x + dx, fOrigin.y + dy);
    ((PolygonFigure)(owner())).scaleRotate(fOrigin, fOrigPoly, fCurrent);
  }

  public void invokeEnd  (int dx, int dy, Drawing drawing) {
    fOrigPoly = null;
    fOrigin = null;
    fCurrent = null;
  }

  public Point locate() {
    if (fCurrent != null)
      return fCurrent;
    else
      return getOrigin();
  }

  Point getOrigin() { // find a nice place to put handle
    // Need to pick a place that will not overlap with point handle
    // and is internal to polygon

    // Try for one HANDLESIZE step away from outermost toward center

    Point outer = ((PolygonFigure)(owner())).outermostPoint();
    Point ctr = ((PolygonFigure)(owner())).center();
    double len = Geom.length(outer.x, outer.y, ctr.x, ctr.y);
    if (len == 0) // best we can do?
      return new Point(outer.x - HANDLESIZE/2, outer.y + HANDLESIZE/2);

    double u = HANDLESIZE / len;
    if (u > 1.0) // best we can do?
      return new Point((outer.x * 3 + ctr.x)/4, (outer.y * 3 + ctr.y)/4);
    else
      return new Point((int)(outer.x * (1.0 - u) + ctr.x * u),
                       (int)(outer.y * (1.0 - u) + ctr.y * u));
  }

  public void draw(Graphics g) {
    Rectangle r = displayBox();

    g.setColor(Color.yellow);
    g.fillOval(r.x, r.y, r.width, r.height);

    g.setColor(Color.black);
    g.drawOval(r.x, r.y, r.width, r.height);

    /*
     * for debugging ...
    Point ctr = ((PolygonFigure)(owner())).center();
    g.setColor(Color.blue);
    g.fillOval(ctr.x, ctr.y, r.width, r.height);

    g.setColor(Color.black);
    g.drawOval(ctr.x, ctr.y, r.width, r.height);

    */
  }
}

