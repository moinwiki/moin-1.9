/*
 * Sun Mar  2 19:15:28 1997  Doug Lea  (dl at gee)
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
 * A Handle to rotate a TriangleFigure
 */
class TriangleRotationHandle extends AbstractHandle {

  private Point fOrigin = null;
  private Point fCenter = null;

  public TriangleRotationHandle(TriangleFigure owner) {
    super(owner);
 }

  public void invokeStart(int  x, int  y, Drawing drawing) {
    fCenter = owner().center();
    fOrigin = getOrigin();
  }

  public void invokeStep (int dx, int dy, Drawing drawing) {
    double angle = Math.atan2(fOrigin.y + dy - fCenter.y,
                              fOrigin.x + dx - fCenter.x);
    ((TriangleFigure)(owner())).rotate(angle);
  }

  public void invokeEnd  (int dx, int dy, Drawing drawing) {
    fOrigin = null;
    fCenter = null;
  }

  public Point locate() {
    return getOrigin();
  }

  Point getOrigin() { // find a nice place to put handle
    // almost same code as PolygonScaleHandle
    Polygon p = ((TriangleFigure)(owner())).polygon();
    Point first = new Point(p.xpoints[0], p.ypoints[0]);
    Point ctr = owner().center();
    double len = Geom.length(first.x, first.y, ctr.x, ctr.y);
    if (len == 0) // best we can do?
      return new Point(first.x - HANDLESIZE/2, first.y + HANDLESIZE/2);

    double u = HANDLESIZE / len;
    if (u > 1.0) // best we can do?
      return new Point((first.x * 3 + ctr.x)/4, (first.y * 3 + ctr.y)/4);
    else
      return new Point((int)(first.x * (1.0 - u) + ctr.x * u),
                       (int)(first.y * (1.0 - u) + ctr.y * u));
  }

  public void draw(Graphics g) {
    Rectangle r = displayBox();

    g.setColor(Color.yellow);
    g.fillOval(r.x, r.y, r.width, r.height);

    g.setColor(Color.black);
    g.drawOval(r.x, r.y, r.width, r.height);
  }
}

