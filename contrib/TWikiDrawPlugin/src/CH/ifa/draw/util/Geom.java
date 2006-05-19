/*
 * @(#)Geom.java 5.1
 *
 */

package CH.ifa.draw.util;

import java.awt.Rectangle;
import java.awt.Point;

/**
 * Some geometric utilities.
 */
public class Geom {

    private Geom() {}; // never instantiated

    /**
     * Tests if a point is on a line.
     */
    static public boolean lineContainsPoint(int x1, int y1,
                            int x2, int y2,
                            int px, int py) {

        Rectangle r = new Rectangle(new Point(x1, y1));
        r.add(x2, y2);

        r.grow(2,2);
        if (! r.contains(px,py))
            return false;

        double a, b, x, y;

        if (x1 == x2)
            return (Math.abs(px - x1) < 3);

        if (y1 == y2)
            return (Math.abs(py - y1) < 3);

        a = (double)(y1 - y2) / (double)(x1 - x2);
        b = (double)y1 - a * (double)x1;
        x = (py - b) / a;
        y = a * px + b;

        return (Math.min(Math.abs(x - px), Math.abs(y - py)) < 4);
    }

    static public final int NORTH = 1;
    static public final int SOUTH = 2;
    static public final int WEST = 3;
    static public final int EAST = 4;

    /**
     * Returns the direction NORTH, SOUTH, WEST, EAST from
     * one point to another one.
     */
    static public int direction(int x1, int y1, int x2, int y2) {
        int direction = 0;
        int vx = x2 - x1;
        int vy = y2 - y1;

        if (vy < vx && vx > -vy)
            direction = EAST;
        else if (vy > vx && vy > -vx)
            direction = NORTH;
        else if (vx < vy && vx < -vy)
            direction = WEST;
        else
            direction = SOUTH;
        return direction;
    }

    static public Point south(Rectangle r) {
        return new Point(r.x + r.width /2, r.y + r.height);
    }

    static public Point center(Rectangle r) {
        return new Point(r.x + r.width /2, r.y + r.height/2);
    }

    static public Point west(Rectangle r) {
        return new Point(r.x, r.y + r.height/ 2);
    }

    static public Point east(Rectangle r) {
        return new Point(r.x+r.width, r.y + r.height/ 2);
    }

    static public Point north(Rectangle r) {
        return new Point(r.x+r.width/2, r.y);
    }

    /**
     * Constains a value to the given range.
     * @return the constrained value
     */
    static public int range(int min, int max, int value) {
        if (value < min)
            value = min;
        if (value > max)
            value = max;
        return value;
    }

    /**
     * Gets the square distance between two points.
     */
    static public long length2(int x1, int y1, int x2, int y2) {
        return (x2-x1)*(x2-x1) + (y2-y1)*(y2-y1);
    }

    /**
     * Gets the distance between to points
     */
    static public long length(int x1, int y1, int x2, int y2) {
        return (long)Math.sqrt(length2(x1, y1, x2, y2));
    }

    /**
     * Gets the angle of a point relative to a rectangle.
     */
    static public double pointToAngle(Rectangle r, Point p) {
        int px = p.x - (r.x+r.width/2);
        int py = p.y - (r.y+r.height/2);
        return Math.atan2(py*r.width, px*r.height);
    }

    /**
     * Gets the point on a rectangle that corresponds to the given angle.
     */
    static public Point angleToPoint(Rectangle r, double angle) {
        double si = Math.sin(angle);
        double co = Math.cos(angle);
        double e = 0.0001;

    	int x= 0, y= 0;
	    if (Math.abs(si) > e) {
		    x= (int) ((1.0 + co/Math.abs(si))/2.0 * r.width);
		    x= range(0, r.width, x);
	    } else if (co >= 0.0)
		    x= r.width;
	    if (Math.abs(co) > e) {
		    y= (int) ((1.0 + si/Math.abs(co))/2.0 * r.height);
		    y= range(0, r.height, y);
	    } else if (si >= 0.0)
		    y= r.height;
	    return new Point(r.x + x, r.y + y);
    }

    /**
     * Converts a polar to a point
     */
    static public Point polarToPoint(double angle, double fx, double fy) {
        double si = Math.sin(angle);
        double co = Math.cos(angle);
	    return new Point((int)(fx*co+0.5), (int)(fy*si+0.5));
    }

    /**
     * Gets the point on an oval that corresponds to the given angle.
     */
    static public Point ovalAngleToPoint(Rectangle r, double angle) {
        Point center = Geom.center(r);
        Point p = Geom.polarToPoint(angle, r.width/2, r.height/2);
        return new Point(center.x + p.x, center.y + p.y);
    }

  /**
   * Standard line intersection algorithm
   * Return the point of intersection if it exists, else null
   **/
   // from Doug Lea's PolygonFigure
  static public Point intersect(int xa, // line 1 point 1 x
                                int ya, // line 1 point 1 y
                                int xb, // line 1 point 2 x
                                int yb, // line 1 point 2 y
                                int xc, // line 2 point 1 x
                                int yc, // line 2 point 1 y
                                int xd, // line 2 point 2 x
                                int yd) { // line 2 point 2 y

    // source: http://vision.dai.ed.ac.uk/andrewfg/c-g-a-faq.html
    // eq: for lines AB and CD
    //     (YA-YC)(XD-XC)-(XA-XC)(YD-YC)
    // r = -----------------------------  (eqn 1)
    //     (XB-XA)(YD-YC)-(YB-YA)(XD-XC)
    //
    //     (YA-YC)(XB-XA)-(XA-XC)(YB-YA)
    // s = -----------------------------  (eqn 2)
    //     (XB-XA)(YD-YC)-(YB-YA)(XD-XC)
    //  XI = XA + r(XB-XA)
    //  YI = YA + r(YB-YA)

    double denom = ((xb - xa) * (yd - yc) - (yb - ya) * (xd - xc));

    double rnum = ((ya - yc) * (xd - xc) - (xa - xc) * (yd - yc));

    if (denom == 0.0) { // parallel
      if (rnum == 0.0) { // coincident; pick one end of first line
        if ((xa < xb && (xb < xc || xb < xd)) ||
            (xa > xb && (xb > xc || xb > xd)))
          return new Point(xb, yb);
        else
          return new Point(xa, ya);
      }
      else
        return null;
    }

    double r = rnum / denom;

    double snum = ((ya - yc) * (xb - xa) - (xa - xc) * (yb - ya));
    double s = snum / denom;

    if (0.0 <= r && r <= 1.0 && 0.0 <= s && s <= 1.0) {
      int px = (int)(xa + (xb - xa) * r);
      int py = (int)(ya + (yb - ya) * r);
      return new Point(px, py);
    }
    else
      return null;
  }

}
